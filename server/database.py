from supabase import create_client, Client
from config import settings
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client: Client = create_client(settings.supabase_url, settings.supabase_key)
    
    # ============================================
    # SESSION OPERATIONS
    # ============================================
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        try:
            response = self.client.table("sessions").select("*").eq("id", session_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def get_active_escalations(self) -> List[Dict[str, Any]]:
        """Get all escalated sessions without assigned agent"""
        try:
            response = self.client.table("sessions")\
                .select("*, users(*)")\
                .eq("status", "escalated")\
                .is_("assigned_agent_id", "null")\
                .order("escalated_at", desc=False)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting escalations: {e}")
            return []
    
    async def get_session_events(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history"""
        try:
            response = self.client.rpc("get_session_history", {
                "p_session_id": session_id,
                "p_limit": limit
            }).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting session events: {e}")
            return []
    
    # ============================================
    # AGENT OPERATIONS
    # ============================================
    
    async def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Update agent online/offline status"""
        try:
            self.client.table("agents").upsert({
                "id": agent_id,
                "status": status,
                "last_active_at": "now()"
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            return False
    
    async def agent_takeover(self, session_id: str, agent_id: str) -> bool:
        """Execute agent takeover"""
        try:
            self.client.rpc("agent_takeover", {
                "p_session_id": session_id,
                "p_agent_id": agent_id
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error in agent takeover: {e}")
            return False
    
    # ============================================
    # ANALYTICS OPERATIONS
    # ============================================
    
    async def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time dashboard metrics"""
        try:
            response = self.client.rpc("get_realtime_metrics").execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"Error getting realtime metrics: {e}")
            return {}
    
    async def get_daily_stats(self, date: str) -> Dict[str, Any]:
        """Get daily statistics"""
        try:
            response = self.client.rpc("get_daily_stats", {"p_date": date}).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return {}
    
    async def get_category_stats(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get category performance stats"""
        try:
            response = self.client.rpc("get_category_stats", {
                "p_start_date": start_date,
                "p_end_date": end_date
            }).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting category stats: {e}")
            return []
    
    async def log_api_cost(
        self, 
        session_id: str, 
        event_id: str,
        service: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float
    ) -> bool:
        """Log API usage cost"""
        try:
            self.client.rpc("log_api_cost", {
                "p_session_id": session_id,
                "p_event_id": event_id,
                "p_service": service,
                "p_model": model,
                "p_input_tokens": input_tokens,
                "p_output_tokens": output_tokens,
                "p_cost_usd": cost_usd
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error logging API cost: {e}")
            return False

# Global database instance
db = Database()