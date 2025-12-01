-- ============================================
-- CORE TABLES
-- ============================================

-- 1. USERS TABLE
-- Tracks unique customers across all channels
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel VARCHAR(20) NOT NULL, -- 'whatsapp', 'telegram', 'web'
  channel_user_id VARCHAR(255) NOT NULL, -- Their ID in that channel
  name VARCHAR(255),
  metadata JSONB DEFAULT '{}', -- Store channel-specific data
  created_at TIMESTAMP DEFAULT NOW(),
  last_seen_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(channel, channel_user_id) -- One user per channel
);

CREATE INDEX idx_users_channel_user_id ON users(channel, channel_user_id);

-- 2. SESSIONS TABLE
-- Each conversation is a session
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  channel VARCHAR(20) NOT NULL,
  selected_category VARCHAR(50), -- NULL until user picks category
  category_selected_at TIMESTAMP,
  status VARCHAR(20) DEFAULT 'active', -- 'active', 'resolved', 'escalated', 'closed'
  assigned_agent_id VARCHAR(100), -- Agent who took over (if escalated)
  escalated_at TIMESTAMP,
  resolved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_assigned_agent ON sessions(assigned_agent_id);

-- 3. EVENTS TABLE
-- Every message and action is an event (immutable log)
CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL, -- 'user_message', 'bot_message', 'agent_message', 'category_selected', 'escalation', 'takeover', 'system'
  sender VARCHAR(20) NOT NULL, -- 'user', 'bot', 'agent', 'system'
  content TEXT,
  metadata JSONB DEFAULT '{}', -- Store extra data (e.g., AI decision reasoning)
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_session_id ON events(session_id);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_created_at ON events(created_at DESC);

-- ============================================
-- ANALYTICS & COST TRACKING TABLES
-- ============================================

-- 4. CONVERSATION_COSTS TABLE
-- Track API costs per conversation
CREATE TABLE conversation_costs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  event_id UUID REFERENCES events(id) ON DELETE CASCADE,
  service VARCHAR(20) NOT NULL, -- 'openai_embedding', 'openai_completion', 'pinecone'
  model VARCHAR(50), -- 'gpt-4', 'gpt-3.5-turbo', 'text-embedding-ada-002'
  input_tokens INT DEFAULT 0,
  output_tokens INT DEFAULT 0,
  total_tokens INT DEFAULT 0,
  cost_usd DECIMAL(10,6) NOT NULL, -- Exact cost in USD
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversation_costs_session_id ON conversation_costs(session_id);
CREATE INDEX idx_conversation_costs_created_at ON conversation_costs(created_at DESC);

-- 5. AI_DECISIONS TABLE
-- Track every AI decision for analytics
CREATE TABLE ai_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  event_id UUID REFERENCES events(id) ON DELETE CASCADE,
  category VARCHAR(50) NOT NULL,
  user_message TEXT NOT NULL,
  bot_response TEXT NOT NULL,
  action VARCHAR(50) NOT NULL, -- 'reply_to_user', 'escalate_to_human', 'ask_clarification'
  escalated BOOLEAN DEFAULT FALSE,
  confidence_score DECIMAL(3,2), -- 0.00 to 1.00 (optional, can extract from LLM)
  response_time_ms INT, -- How long the AI took to respond
  retrieval_docs_count INT, -- How many Pinecone docs were retrieved
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_decisions_session_id ON ai_decisions(session_id);
CREATE INDEX idx_ai_decisions_category ON ai_decisions(category);
CREATE INDEX idx_ai_decisions_escalated ON ai_decisions(escalated);
CREATE INDEX idx_ai_decisions_created_at ON ai_decisions(created_at DESC);

-- 6. USER_FEEDBACK TABLE
-- Post-conversation ratings (optional feature)
CREATE TABLE user_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  rating INT CHECK (rating >= 1 AND rating <= 5), -- 1-5 stars
  comment TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_feedback_session_id ON user_feedback(session_id);
CREATE INDEX idx_user_feedback_rating ON user_feedback(rating);

-- 7. AGENTS TABLE
-- Track human agents
CREATE TABLE agents (
  id VARCHAR(100) PRIMARY KEY, -- agent_id from JWT
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE,
  status VARCHAR(20) DEFAULT 'offline', -- 'online', 'offline', 'busy'
  current_sessions INT DEFAULT 0, -- How many sessions they're handling
  total_takeovers INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  last_active_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agents_status ON agents(status);

-- ============================================
-- RPC FUNCTIONS (Stored Procedures)
-- ============================================

-- FUNCTION 1: Create or Get Session
-- Called at start of every conversation
CREATE OR REPLACE FUNCTION create_or_get_session(
  p_channel VARCHAR,
  p_channel_user_id VARCHAR,
  p_user_name VARCHAR DEFAULT NULL
)
RETURNS TABLE(
  session_id UUID,
  user_id UUID,
  selected_category VARCHAR,
  status VARCHAR
) SET search_path = public AS $$
DECLARE
  v_user_id UUID;
  v_session_id UUID;
BEGIN
  -- Get or create user
  INSERT INTO users (channel, channel_user_id, name, last_seen_at)
  VALUES (p_channel, p_channel_user_id, p_user_name, NOW())
  ON CONFLICT (channel, channel_user_id) 
  DO UPDATE SET 
    last_seen_at = NOW(),
    name = COALESCE(EXCLUDED.name, users.name)
  RETURNING id INTO v_user_id;

  -- Get active session or create new one
  SELECT id INTO v_session_id
  FROM sessions
  WHERE user_id = v_user_id
    AND status IN ('active', 'escalated')
  ORDER BY created_at DESC
  LIMIT 1;

  -- Create new session if none exists
  IF v_session_id IS NULL THEN
    INSERT INTO sessions (user_id, channel, status)
    VALUES (v_user_id, p_channel, 'active')
    RETURNING id INTO v_session_id;
  END IF;

  -- Update session timestamp
  UPDATE sessions 
  SET updated_at = NOW() 
  WHERE id = v_session_id;

  -- Return session details
  RETURN QUERY
  SELECT 
    s.id AS session_id,
    s.user_id,
    s.selected_category,
    s.status
  FROM sessions s
  WHERE s.id = v_session_id;
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 2: Log Event
-- Append event to session
CREATE OR REPLACE FUNCTION log_event(
  p_session_id UUID,
  p_type VARCHAR,
  p_sender VARCHAR,
  p_content TEXT,
  p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID SET search_path = public AS $$
DECLARE
  v_event_id UUID;
BEGIN
  INSERT INTO events (session_id, type, sender, content, metadata)
  VALUES (p_session_id, p_type, p_sender, p_content, p_metadata)
  RETURNING id INTO v_event_id;

  -- Update session timestamp
  UPDATE sessions SET updated_at = NOW() WHERE id = p_session_id;

  RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 3: Set Category
-- User selects category
CREATE OR REPLACE FUNCTION set_session_category(
  p_session_id UUID,
  p_category VARCHAR
)
RETURNS BOOLEAN SET search_path = public AS $$
BEGIN
  UPDATE sessions
  SET 
    selected_category = p_category,
    category_selected_at = NOW(),
    updated_at = NOW()
  WHERE id = p_session_id;

  RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 4: Escalate Session
-- Mark session as escalated
CREATE OR REPLACE FUNCTION escalate_session(
  p_session_id UUID,
  p_reason TEXT DEFAULT NULL
)
RETURNS BOOLEAN SET search_path = public AS $$
BEGIN
  UPDATE sessions
  SET 
    status = 'escalated',
    escalated_at = NOW(),
    updated_at = NOW()
  WHERE id = p_session_id;

  -- Log escalation event
  INSERT INTO events (session_id, type, sender, content)
  VALUES (p_session_id, 'escalation', 'system', p_reason);

  RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 5: Agent Takeover
-- Assign agent to session
CREATE OR REPLACE FUNCTION agent_takeover(
  p_session_id UUID,
  p_agent_id VARCHAR
)
RETURNS BOOLEAN SET search_path = public AS $$
BEGIN
  UPDATE sessions
  SET 
    assigned_agent_id = p_agent_id,
    updated_at = NOW()
  WHERE id = p_session_id;

  -- Log takeover event
  INSERT INTO events (session_id, type, sender, content, metadata)
  VALUES (
    p_session_id, 
    'takeover', 
    'system', 
    'Agent took over conversation',
    jsonb_build_object('agent_id', p_agent_id)
  );

  -- Update agent stats
  UPDATE agents
  SET 
    current_sessions = current_sessions + 1,
    total_takeovers = total_takeovers + 1,
    status = 'busy',
    last_active_at = NOW()
  WHERE id = p_agent_id;

  RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 6: Get Session History
-- Retrieve all events for a session
CREATE OR REPLACE FUNCTION get_session_history(
  p_session_id UUID,
  p_limit INT DEFAULT 50
)
RETURNS TABLE(
  event_id UUID,
  type VARCHAR,
  sender VARCHAR,
  content TEXT,
  metadata JSONB,
  created_at TIMESTAMP
) SET search_path = public AS $$
BEGIN
  RETURN QUERY
  SELECT 
    id AS event_id,
    e.type,
    e.sender,
    e.content,
    e.metadata,
    e.created_at
  FROM events e
  WHERE session_id = p_session_id
  ORDER BY created_at ASC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 7: Log API Cost
-- Track cost of each API call
CREATE OR REPLACE FUNCTION log_api_cost(
  p_session_id UUID,
  p_event_id UUID,
  p_service VARCHAR,
  p_model VARCHAR,
  p_input_tokens INT,
  p_output_tokens INT,
  p_cost_usd DECIMAL
)
RETURNS UUID SET search_path = public AS $$
DECLARE
  v_cost_id UUID;
BEGIN
  INSERT INTO conversation_costs (
    session_id, 
    event_id, 
    service, 
    model, 
    input_tokens, 
    output_tokens, 
    total_tokens,
    cost_usd
  )
  VALUES (
    p_session_id,
    p_event_id,
    p_service,
    p_model,
    p_input_tokens,
    p_output_tokens,
    p_input_tokens + p_output_tokens,
    p_cost_usd
  )
  RETURNING id INTO v_cost_id;

  RETURN v_cost_id;
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 8: Dashboard - Real-time Metrics
-- Get current system stats
CREATE OR REPLACE FUNCTION get_realtime_metrics()
RETURNS TABLE(
  active_sessions INT,
  messages_last_hour INT,
  escalations_pending INT,
  agents_online INT,
  avg_response_time_ms INT
) SET search_path = public AS $$
BEGIN
  RETURN QUERY
  SELECT
    (SELECT COUNT(*) FROM sessions WHERE status = 'active')::INT,
    (SELECT COUNT(*) FROM events WHERE created_at > NOW() - INTERVAL '1 hour')::INT,
    (SELECT COUNT(*) FROM sessions WHERE status = 'escalated' AND assigned_agent_id IS NULL)::INT,
    (SELECT COUNT(*) FROM agents WHERE status = 'online')::INT,
    (SELECT AVG(response_time_ms)::INT FROM ai_decisions WHERE created_at > NOW() - INTERVAL '1 hour')::INT;
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 9: Dashboard - Daily Stats
-- Aggregate stats for owner dashboard
CREATE OR REPLACE FUNCTION get_daily_stats(p_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE(
  total_conversations INT,
  ai_resolved INT,
  human_escalations INT,
  ai_resolution_rate DECIMAL,
  total_cost_usd DECIMAL,
  avg_cost_per_conversation DECIMAL
) SET search_path = public AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(DISTINCT s.id)::INT AS total_conversations,
    COUNT(DISTINCT CASE WHEN s.status = 'resolved' AND s.assigned_agent_id IS NULL THEN s.id END)::INT AS ai_resolved,
    COUNT(DISTINCT CASE WHEN s.escalated_at IS NOT NULL THEN s.id END)::INT AS human_escalations,
    ROUND(
      COUNT(DISTINCT CASE WHEN s.status = 'resolved' AND s.assigned_agent_id IS NULL THEN s.id END)::DECIMAL / 
      NULLIF(COUNT(DISTINCT s.id), 0) * 100, 
      2
    ) AS ai_resolution_rate,
    COALESCE(SUM(cc.cost_usd), 0) AS total_cost_usd,
    ROUND(
      COALESCE(SUM(cc.cost_usd), 0) / NULLIF(COUNT(DISTINCT s.id), 0),
      4
    ) AS avg_cost_per_conversation
  FROM sessions s
  LEFT JOIN conversation_costs cc ON cc.session_id = s.id
  WHERE DATE(s.created_at) = p_date;
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 10: Dashboard - Category Performance
CREATE OR REPLACE FUNCTION get_category_stats(
  p_start_date DATE DEFAULT CURRENT_DATE - INTERVAL '7 days',
  p_end_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
  category VARCHAR,
  total_messages INT,
  ai_resolved_pct DECIMAL,
  total_cost_usd DECIMAL
) SET search_path = public AS $$
BEGIN
  RETURN QUERY
  SELECT
    s.selected_category AS category,
    COUNT(ad.id)::INT AS total_messages,
    ROUND(
      (COUNT(CASE WHEN ad.escalated = FALSE THEN 1 END)::DECIMAL / NULLIF(COUNT(ad.id), 0)) * 100,
      1
    ) AS ai_resolved_pct,
    COALESCE(SUM(cc.cost_usd), 0) AS total_cost_usd
  FROM sessions s
  LEFT JOIN ai_decisions ad ON ad.session_id = s.id
  LEFT JOIN conversation_costs cc ON cc.session_id = s.id
  WHERE s.created_at BETWEEN p_start_date AND p_end_date
    AND s.selected_category IS NOT NULL
  GROUP BY s.selected_category
  ORDER BY total_messages DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- 1. Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_costs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

-- 2. Agent Policies (Authenticated Users)
-- Assumes agents are authenticated via Supabase Auth

-- USERS: Agents can view all users
CREATE POLICY "Agents can view users" ON users
  FOR SELECT TO authenticated USING (true);

-- SESSIONS: Agents can view all sessions and update them (takeover/resolve)
CREATE POLICY "Agents can view sessions" ON sessions
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Agents can update sessions" ON sessions
  FOR UPDATE TO authenticated USING (true);

-- EVENTS: Agents can view events and insert new ones (messages)
CREATE POLICY "Agents can view events" ON events
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Agents can insert events" ON events
  FOR INSERT TO authenticated WITH CHECK (true);

-- ANALYTICS TABLES: Agents can view for dashboard
CREATE POLICY "Agents can view costs" ON conversation_costs
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Agents can view decisions" ON ai_decisions
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Agents can view feedback" ON user_feedback
  FOR SELECT TO authenticated USING (true);

-- AGENTS: View all agents (team status), Update own status
CREATE POLICY "Agents can view team" ON agents
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Agents can update own status" ON agents
  FOR UPDATE TO authenticated USING ((select auth.uid())::text = id);