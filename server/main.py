from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime, timedelta, date
import httpx
from typing import List, Optional, Dict, Any
import json

from config import settings
from database import db
from websocket_manager import manager
from models import (
    WebWidgetMessage, EscalationPayload, HumanTakeoverRequest, 
    AgentMessageRequest, RealtimeMetrics, DailyStats, CategoryStats
)
from auth import verify_agent_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Support Platform API",
    description="Backend for multi-channel AI customer support",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Support Platform API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "agents_connected": manager.get_connected_count(),
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# WEB WIDGET WEBHOOK
# ============================================

@app.post("/webhook/web-message")
async def receive_web_message(message: WebWidgetMessage):
    """
    Receive message from website chat widget
    Forward to n8n inbound handler
    """
    try:
        # Prepare payload for n8n
        n8n_payload = {
            "channel": "web",
            "user_id": message.user_id,
            "message": message.message,
            "user_name": message.user_name,
            "metadata": message.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Forward to n8n webhook
        n8n_url = f"{settings.n8n_webhook_base_url}/inbound-web"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(n8n_url, json=n8n_payload)
            response.raise_for_status()
        
        logger.info(f"Web message forwarded to n8n from user {message.user_id}")
        
        return {
            "success": True,
            "message": "Message received and forwarded",
            "user_id": message.user_id
        }
    
    except httpx.HTTPError as e:
        logger.error(f"Error forwarding web message to n8n: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to forward message to processing pipeline"
        )
    except Exception as e:
        logger.error(f"Unexpected error in web message handler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================
# ESCALATION WEBHOOK (from n8n)
# ============================================

@app.post("/escalations")
async def receive_escalation(escalation: EscalationPayload):
    """
    Receive escalation from n8n
    Broadcast to all connected agents via WebSocket
    """
    try:
        # Get full session details
        session = await db.get_session(escalation.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get conversation history
        events = await db.get_session_events(escalation.session_id, limit=10)
        
        # Prepare escalation data for agents
        escalation_data = {
            "session_id": escalation.session_id,
            "user_id": escalation.user_id,
            "channel": escalation.channel,
            "category": escalation.category,
            "reason": escalation.reason,
            "conversation_summary": escalation.conversation_summary,
            "recent_messages": events[-5:] if events else [],  # Last 5 messages
            "escalated_at": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all agents
        await manager.broadcast_escalation(escalation_data)
        
        logger.info(f"Escalation broadcasted for session {escalation.session_id}")
        
        return {
            "success": True,
            "session_id": escalation.session_id,
            "agents_notified": manager.get_connected_count()
        }
    
    except Exception as e:
        logger.error(f"Error handling escalation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ============================================
# HUMAN TAKEOVER
# ============================================

@app.post("/human-takeover")
async def human_takeover(request: HumanTakeoverRequest, agent_info: dict = Depends(verify_agent_token)):
    """
    Agent takes over a conversation
    """
    try:
        # Verify agent matches token
        if request.agent_id != agent_info["agent_id"]:
            raise HTTPException(status_code=403, detail="Agent ID mismatch")
        
        # Execute takeover in database
        success = await db.agent_takeover(request.session_id, request.agent_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to execute takeover")
        
        # Notify n8n to stop AI responses for this session
        n8n_url = f"{settings.n8n_webhook_base_url}/{settings.n8n_takeover_webhook}"
        
        takeover_payload = {
            "session_id": request.session_id,
            "agent_id": request.agent_id,
            "agent_name": request.agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(n8n_url, json=takeover_payload)
        
        # Notify agent via WebSocket
        await manager.send_to_agent(request.agent_id, {
            "type": "takeover_success",
            "payload": {
                "session_id": request.session_id,
                "message": "Takeover successful"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Agent {request.agent_id} took over session {request.session_id}")
        
        return {
            "success": True,
            "session_id": request.session_id,
            "agent_id": request.agent_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in human takeover: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ============================================
# AGENT MESSAGE SENDING
# ============================================

@app.post("/send-message")
async def send_agent_message(request: AgentMessageRequest, agent_info: dict = Depends(verify_agent_token)):
    """
    Agent sends message to user
    Forward to n8n for delivery
    """
    try:
        # Verify agent matches token
        if request.agent_id != agent_info["agent_id"]:
            raise HTTPException(status_code=403, detail="Agent ID mismatch")
        
        # Forward to n8n agent message bridge
        n8n_url = f"{settings.n8n_webhook_base_url}/{settings.n8n_agent_message_webhook}"
        
        message_payload = {
            "session_id": request.session_id,
            "agent_id": request.agent_id,
            "message": request.message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(n8n_url, json=message_payload)
            response.raise_for_status()
        
        logger.info(f"Agent message sent: session={request.session_id}, agent={request.agent_id}")
        
        return {
            "success": True,
            "session_id": request.session_id,
            "message_delivered": True
        }
    
    except httpx.HTTPError as e:
        logger.error(f"Error sending agent message: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to forward message to n8n"
        )

@app.websocket("/ws/agent/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket connection for agents to receive real-time updates
    """
    await manager.connect(agent_id, websocket)
    
    # Update agent status to online
    await db.update_agent_status(agent_id, "online")
    
    try:
        # Send current escalations on connect
        escalations = await db.get_active_escalations()
        if escalations:
            await manager.send_to_agent(agent_id, {
                "type": "initial_escalations",
                "payload": escalations,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            # Handle ping/pong for keepalive
            if data.get("type") == "ping":
                await manager.send_to_agent(agent_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(agent_id)
        await db.update_agent_status(agent_id, "offline")
        logger.info(f"Agent {agent_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        manager.disconnect(agent_id)
        await db.update_agent_status(agent_id, "offline")

# ============================================
# BOT MESSAGE SENDING (from n8n)
# ============================================

class BotMessageRequest(BaseModel):
    session_id: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

@app.post("/send-bot-message")
async def send_bot_message(request: BotMessageRequest):
    """
    Receive bot response from n8n
    Push to user via WebSocket
    """
    try:
        # Send to user via WebSocket
        await manager.send_to_user(request.session_id, {
            "type": "bot_message",
            "payload": {
                "message": request.message,
                "metadata": request.metadata
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Bot message sent to user {request.session_id}")
        
        return {
            "success": True,
            "session_id": request.session_id
        }
    except Exception as e:
        logger.error(f"Error sending bot message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message to user")

# ============================================
# USER WEBSOCKET
# ============================================

@app.websocket("/ws/chat/{session_id}")
async def user_websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket connection for web users
    """
    await manager.connect_user(session_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle ping/pong
            if data.get("type") == "ping":
                await manager.send_to_user(session_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect_user(session_id)
        logger.info(f"User {session_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {session_id}: {e}")
        manager.disconnect_user(session_id)

# ============================================
# ANALYTICS ENDPOINTS (for Owner Dashboard)
# ============================================

@app.get("/api/dashboard/daily", response_model=DailyStats)
async def get_daily_stats(target_date: str = None):
    """Get daily statistics"""
    try:
        if not target_date:
            target_date = date.today().isoformat()
        
        stats = await db.get_daily_stats(target_date)
        
        return DailyStats(
            date=target_date,
            total_conversations=stats.get("total_conversations", 0),
            ai_resolved=stats.get("ai_resolved", 0),
            human_escalations=stats.get("human_escalations", 0),
            ai_resolution_rate=float(stats.get("ai_resolution_rate", 0)),
            total_cost_usd=float(stats.get("total_cost_usd", 0)),
            avg_cost_per_conversation=float(stats.get("avg_cost_per_conversation", 0))
        )
    except Exception as e:
        logger.error(f"Error getting daily stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch daily stats")

@app.get("/api/dashboard/categories", response_model=List[CategoryStats])
async def get_category_performance(days: int = 7):
    """Get category performance over time"""
    try:
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        stats = await db.get_category_stats(start_date, end_date)
        
        return [
            CategoryStats(
                category=item["category"],
                total_messages=item["total_messages"],
                ai_resolved_pct=float(item["ai_resolved_pct"]),
                total_cost_usd=float(item["total_cost_usd"])
            )
            for item in stats
        ]
    except Exception as e:
        logger.error(f"Error getting category stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch category stats")

@app.get("/api/dashboard/conversations")
async def get_recent_conversations(limit: int = 50, status: str = None):
    """Get recent conversations with details"""
    try:
        query = db.client.table("sessions")\
            .select("*, users(*)")\
            .order("created_at", desc=True)\
            .limit(limit)
        
        if status:
            query = query.eq("status", status)
        
        response = query.execute()
        
        return {
            "conversations": response.data,
            "count": len(response.data)
        }
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")

@app.get("/api/dashboard/conversation/{session_id}")
async def get_conversation_detail(session_id: str):
    """Get detailed conversation history"""
    try:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        events = await db.get_session_events(session_id, limit=100)
        
        # Get total cost for this conversation
        cost_response = db.client.table("conversation_costs")\
            .select("cost_usd")\
            .eq("session_id", session_id)\
            .execute()
        
        total_cost = sum(item["cost_usd"] for item in cost_response.data)
        
        return {
            "session": session,
            "events": events,
            "total_cost": total_cost,
            "message_count": len(events)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversation")

@app.get("/api/dashboard/costs/summary")
async def get_cost_summary(days: int = 30):
    """Get cost summary over time period"""
    try:
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Total costs by service
        service_costs = db.client.table("conversation_costs")\
            .select("service, cost_usd")\
            .gte("created_at", start_date)\
            .execute()
        
        # Aggregate by service
        cost_by_service = {}
        total_cost = 0
        
        for item in service_costs.data:
            service = item["service"]
            cost = item["cost_usd"]
            cost_by_service[service] = cost_by_service.get(service, 0) + cost
            total_cost += cost
        
        # Daily costs
        daily_costs = db.client.table("conversation_costs")\
            .select("created_at, cost_usd")\
            .gte("created_at", start_date)\
            .order("created_at", desc=False)\
            .execute()
        
        # Group by day
        daily_aggregated = {}
        for item in daily_costs.data:
            day = item["created_at"][:10]  # YYYY-MM-DD
            daily_aggregated[day] = daily_aggregated.get(day, 0) + item["cost_usd"]
        
        return {
            "period_days": days,
            "total_cost": round(total_cost, 2),
            "cost_by_service": {k: round(v, 4) for k, v in cost_by_service.items()},
            "daily_costs": [
                {"date": day, "cost": round(cost, 4)} 
                for day, cost in sorted(daily_aggregated.items())
            ]
        }
    except Exception as e:
        logger.error(f"Error getting cost summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cost summary")

# ============================================
# COST TRACKING ENDPOINT (called by n8n)
# ============================================

@app.post("/api/log-cost")
async def log_api_cost_endpoint(
    session_id: str,
    event_id: str,
    service: str,
    model: str,
    input_tokens: int,
    output_tokens: int = 0
):
    """
    Log API usage cost (called by n8n after each LLM/embedding call)
    """
    try:
        # Calculate cost
        if service.startswith("openai"):
            cost = calculate_openai_cost(model, input_tokens, output_tokens)
        else:
            cost = 0.0001  # Default small cost for other services
        
        # Log to database
        success = await db.log_api_cost(
            session_id=session_id,
            event_id=event_id,
            service=service,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost
        )
        
        if not success:
            raise Exception("Failed to log cost to database")
        
        return {
            "success": True,
            "cost_usd": cost,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error logging API cost: {e}")
        raise HTTPException(status_code=500, detail="Failed to log cost")

# ============================================
# AGENT MANAGEMENT
# ============================================

@app.get("/api/agents")
async def get_agents():
    """Get all agents and their status"""
    try:
        response = db.client.table("agents")\
            .select("*")\
            .order("name")\
            .execute()
        
        # Update online status based on WebSocket connections
        agents = response.data
        for agent in agents:
            agent["is_connected"] = agent["id"] in manager.connected_agents
        
        return {
            "agents": agents,
            "online_count": manager.get_connected_count()
        }
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agents")

@app.get("/api/sessions/active")
async def get_active_sessions():
    """Get all active sessions"""
    try:
        response = db.client.table("sessions")\
            .select("*, users(*)")\
            .in_("status", ["active", "escalated"])\
            .order("updated_at", desc=True)\
            .execute()
        
        return {
            "sessions": response.data,
            "count": len(response.data)
        }
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch active sessions")

# ============================================
# STARTUP/SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run on server startup"""
    logger.info("🚀 AI Support Platform API starting...")
    logger.info(f"📍 Server: {settings.api_host}:{settings.api_port}")
    logger.info(f"🔗 Supabase: {settings.supabase_url}")
    logger.info(f"🔗 n8n: {settings.n8n_webhook_base_url}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on server shutdown"""
    logger.info("🛑 AI Support Platform API shutting down...")
    
    # Disconnect all agents
    for agent_id in list(manager.connected_agents):
        await db.update_agent_status(agent_id, "offline")

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )