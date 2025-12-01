from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# ============================================
# INCOMING MESSAGE MODELS
# ============================================

class WebWidgetMessage(BaseModel):
    """Message from website chat widget"""
    user_id: str = Field(..., description="Unique ID for web user (generated client-side)")
    message: str = Field(..., min_length=1, max_length=4000)
    user_name: Optional[str] = Field(None, description="Optional user name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class EscalationPayload(BaseModel):
    """Escalation event from n8n"""
    session_id: str
    user_id: str
    channel: str
    category: str
    reason: Optional[str] = None
    conversation_summary: Optional[str] = None
    last_messages: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    """WebSocket message structure"""
    type: str  # 'escalation', 'takeover_success', 'new_message', 'error', 'ping'
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ============================================
# ANALYTICS MODELS
# ============================================

class RealtimeMetrics(BaseModel):
    active_sessions: int
    messages_last_hour: int
    escalations_pending: int
    agents_online: int
    avg_response_time_ms: Optional[int]

class DailyStats(BaseModel):
    date: str
    total_conversations: int
    ai_resolved: int
    human_escalations: int
    ai_resolution_rate: float
    total_cost_usd: float
    avg_cost_per_conversation: float

class CategoryStats(BaseModel):
    category: str
    total_messages: int
    ai_resolved_pct: float
    total_cost_usd: float

class ConversationDetail(BaseModel):
    session_id: str
    user_id: str
    channel: str
    category: Optional[str]
    status: str
    message_count: int
    total_cost: float
    created_at: datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# ============================================
# INCOMING MESSAGE MODELS
# ============================================

class WebWidgetMessage(BaseModel):
    """Message from website chat widget"""
    user_id: str = Field(..., description="Unique ID for web user (generated client-side)")
    message: str = Field(..., min_length=1, max_length=4000)
    user_name: Optional[str] = Field(None, description="Optional user name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class EscalationPayload(BaseModel):
    """Escalation event from n8n"""
    session_id: str
    user_id: str
    channel: str
    category: str
    reason: Optional[str] = None
    conversation_summary: Optional[str] = None
    last_messages: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    """WebSocket message structure"""
    type: str  # 'escalation', 'takeover_success', 'new_message', 'error', 'ping'
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ============================================
# ANALYTICS MODELS
# ============================================

class RealtimeMetrics(BaseModel):
    active_sessions: int
    messages_last_hour: int
    escalations_pending: int
    agents_online: int
    avg_response_time_ms: Optional[int]

class DailyStats(BaseModel):
    date: str
    total_conversations: int
    ai_resolved: int
    human_escalations: int
    ai_resolution_rate: float
    total_cost_usd: float
    avg_cost_per_conversation: float

class CategoryStats(BaseModel):
    category: str
    total_messages: int
    ai_resolved_pct: float
    total_cost_usd: float

class ConversationDetail(BaseModel):
    session_id: str
    user_id: str
    channel: str
    category: Optional[str]
    status: str
    message_count: int
    total_cost: float
    created_at: datetime
    resolved_at: Optional[datetime]

# ============================================
# COST TRACKING MODELS
# ============================================

class APIUsage(BaseModel):
    """Track API usage for cost calculation"""
    service: str  # 'openai_embedding', 'openai_completion', 'pinecone'
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float

class HumanTakeoverRequest(BaseModel):
    session_id: str
    agent_id: str
    agent_name: str

class AgentMessageRequest(BaseModel):
    session_id: str
    agent_id: str
    message: str