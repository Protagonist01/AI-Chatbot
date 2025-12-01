from fastapi import WebSocket
from typing import Dict, Set
# import json
import logging
from datetime import datetime
from fastapi import WebSocket
from typing import Dict, Set
# import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections for agents"""
    
    def __init__(self):
        # agent_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # session_id -> WebSocket connection
        self.active_user_connections: Dict[str, WebSocket] = {}
        # Track which agents are connected
        self.connected_agents: Set[str] = set()
    
    async def connect(self, agent_id: str, websocket: WebSocket):
        """Connect a new agent"""
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.connected_agents.add(agent_id)
        logger.info(f"Agent {agent_id} connected. Total agents: {len(self.connected_agents)}")
        
        # Send welcome message
        await self.send_to_agent(agent_id, {
            "type": "connected",
            "payload": {
                "agent_id": agent_id,
                "message": "Connected successfully"
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    async def connect_user(self, session_id: str, websocket: WebSocket):
        """Connect a new user"""
        await websocket.accept()
        self.active_user_connections[session_id] = websocket
        logger.info(f"User {session_id} connected. Total users: {len(self.active_user_connections)}")
        
        # Send welcome message
        await self.send_to_user(session_id, {
            "type": "connected",
            "payload": {
                "session_id": session_id,
                "message": "Connected successfully"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, agent_id: str):
        """Disconnect an agent"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        if agent_id in self.connected_agents:
            self.connected_agents.remove(agent_id)
        logger.info(f"Agent {agent_id} disconnected. Total agents: {len(self.connected_agents)}")

    def disconnect_user(self, session_id: str):
        """Disconnect a user"""
        if session_id in self.active_user_connections:
            del self.active_user_connections[session_id]
        logger.info(f"User {session_id} disconnected. Total users: {len(self.active_user_connections)}")
    
    async def send_to_agent(self, agent_id: str, message: dict):
        """Send message to specific agent"""
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to agent {agent_id}: {e}")
                self.disconnect(agent_id)

    async def send_to_user(self, session_id: str, message: dict):
        """Send message to specific user"""
        if session_id in self.active_user_connections:
            try:
                await self.active_user_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {session_id}: {e}")
                self.disconnect_user(session_id)
    
    async def broadcast(self, message: dict, exclude: Set[str] = None):
        """Broadcast message to all connected agents"""
        exclude = exclude or set()
        
        disconnected = []
        for agent_id, connection in self.active_connections.items():
            if agent_id not in exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to agent {agent_id}: {e}")
                    disconnected.append(agent_id)
        
        # Clean up disconnected agents
        for agent_id in disconnected:
            self.disconnect(agent_id)
    
    async def broadcast_escalation(self, escalation_data: dict):
        """Broadcast new escalation to all agents"""
        message = {
            "type": "escalation",
            "payload": escalation_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
        logger.info(f"Broadcasted escalation for session {escalation_data.get('session_id')}")
    
    def get_connected_count(self) -> int:
        """Get number of connected agents"""
        return len(self.connected_agents)

# Global connection manager instance
manager = ConnectionManager()