import React, { useState, useEffect, useRef } from 'react'
import LoginScreen from './components/LoginScreen'
import ConnectionStatus from './components/ConnectionStatus'
import EscalationCard from './components/EscalationCard'
import ChatInterface from './components/ChatInterface'

const API_BASE = import.meta.env.VITE_API_BASE_URL
const WS_BASE = import.meta.env.VITE_WS_BASE_URL

function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [agentToken, setAgentToken] = useState(null)
  const [agentInfo, setAgentInfo] = useState(null)

  // WebSocket state
  const [ws, setWs] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const reconnectTimeoutRef = useRef(null)

  // Escalations state
  const [escalations, setEscalations] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [conversationHistory, setConversationHistory] = useState([])
  
  // UI state
  const [notification, setNotification] = useState(null)

  // Parse JWT to get agent info
  const parseJWT = (token) => {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      return JSON.parse(jsonPayload)
    } catch (e) {
      console.error('Failed to parse JWT:', e)
      return null
    }
  }

  // Handle login
  const handleLogin = (token) => {
    const payload = parseJWT(token)
    if (!payload) {
      showNotification('Invalid token', 'error')
      return
    }

    setAgentToken(token)
    setAgentInfo({
      id: payload.sub,
      name: payload.name
    })
    setIsAuthenticated(true)
    localStorage.setItem('agent_token', token)
  }

  // Handle logout
  const handleLogout = () => {
    if (ws) {
      ws.close()
    }
    setIsAuthenticated(false)
    setAgentToken(null)
    setAgentInfo(null)
    setEscalations([])
    setSelectedSession(null)
    localStorage.removeItem('agent_token')
  }

  // Show notification
  const showNotification = (message, type = 'info') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }

  // Connect to WebSocket
  const connectWebSocket = () => {
    if (!agentInfo) return

    const wsUrl = `${WS_BASE}/ws/agent/${agentInfo.id}`
    console.log('Connecting to WebSocket:', wsUrl)

    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      setConnectionStatus('connected')
      setWs(websocket)
      showNotification('Connected to support system', 'success')
    }

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('WebSocket message:', message)

        switch (message.type) {
          case 'connected':
            console.log('Connection confirmed:', message.payload.message)
            break

          case 'initial_escalations':
            // Load existing escalations on connect
            setEscalations(message.payload || [])
            break

          case 'escalation':
            // New escalation received
            const newEscalation = message.payload
            setEscalations(prev => {
              // Avoid duplicates
              if (prev.some(e => e.session_id === newEscalation.session_id)) {
                return prev
              }
              return [...prev, newEscalation]
            })
            showNotification('New escalation received!', 'warning')
            // Play notification sound (optional)
            playNotificationSound()
            break

          case 'takeover_success':
            showNotification('Takeover successful', 'success')
            break

          case 'pong':
            // Keepalive response
            break

          case 'error':
            showNotification(message.payload.message || 'Error occurred', 'error')
            break

          default:
            console.log('Unknown message type:', message.type)
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnectionStatus('error')
      showNotification('Connection error', 'error')
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setConnectionStatus('disconnected')
      setWs(null)
      showNotification('Disconnected from support system', 'warning')

      // Auto-reconnect after 5 seconds
      if (isAuthenticated) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connectWebSocket()
        }, 5000)
      }
    }
  }

  // Play notification sound
  const playNotificationSound = () => {
    try {
      const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZAAA=')
      audio.play().catch(e => console.log('Could not play sound:', e))
    } catch (e) {
      console.log('Audio not supported')
    }
  }

  // Send keepalive ping every 30 seconds
  useEffect(() => {
    if (ws && connectionStatus === 'connected') {
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)

      return () => clearInterval(pingInterval)
    }
  }, [ws, connectionStatus])

  // Handle takeover
  const handleTakeover = async (sessionId) => {
    if (!agentToken || !agentInfo) return

    try {
      const response = await fetch(`${API_BASE}/human-takeover`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${agentToken}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          agent_id: agentInfo.id,
          agent_name: agentInfo.name
        })
      })

      if (!response.ok) {
        throw new Error('Takeover failed')
      }

      // Remove from escalations list
      setEscalations(prev => prev.filter(e => e.session_id !== sessionId))
      
      // Set as active session
      setSelectedSession(sessionId)
      
      // Load conversation history
      await loadConversationHistory(sessionId)

      showNotification('You are now handling this conversation', 'success')
    } catch (error) {
      console.error('Takeover error:', error)
      showNotification('Failed to take over conversation', 'error')
    }
  }

  // Load conversation history
  const loadConversationHistory = async (sessionId) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/dashboard/conversation/${sessionId}`
      )
      
      if (!response.ok) throw new Error('Failed to load history')
      
      const data = await response.json()
      setConversationHistory(data.events || [])
    } catch (error) {
      console.error('Failed to load conversation:', error)
      showNotification('Failed to load conversation history', 'error')
    }
  }

  // Send message to user
  const handleSendMessage = async (message) => {
    if (!selectedSession || !agentToken) return

    try {
      const response = await fetch(`${API_BASE}/send-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${agentToken}`
        },
        body: JSON.stringify({
          session_id: selectedSession,
          agent_id: agentInfo.id,
          message: message
        })
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      // Add message to local conversation history
      setConversationHistory(prev => [...prev, {
        event_id: Date.now(),
        type: 'agent_message',
        sender: 'agent',
        content: message,
        created_at: new Date().toISOString()
      }])

      showNotification('Message sent', 'success')
    } catch (error) {
      console.error('Send message error:', error)
      showNotification('Failed to send message', 'error')
    }
  }

  // Close current session
  const handleCloseSession = () => {
    setSelectedSession(null)
    setConversationHistory([])
  }

  // Connect WebSocket when authenticated
  useEffect(() => {
    if (isAuthenticated && agentInfo) {
      connectWebSocket()
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (ws) {
        ws.close()
      }
    }
  }, [isAuthenticated, agentInfo])

  // Check for saved token on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('agent_token')
    if (savedToken) {
      handleLogin(savedToken)
    }
  }, [])

  // Render login screen if not authenticated
  if (!isAuthenticated) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>🎧 Agent Console</h1>
          <div className="header-right">
            <ConnectionStatus status={connectionStatus} />
            <div className="agent-info">
              <span className="agent-name">{agentInfo.name}</span>
              <button onClick={handleLogout} className="btn-logout">
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div className={`notification notification-${notification.type}`}>
          {notification.message}
        </div>
      )}

      {/* Main Content */}
      <main className="main-content">
        {selectedSession ? (
          // Chat Interface
          <ChatInterface
            sessionId={selectedSession}
            messages={conversationHistory}
            onSendMessage={handleSendMessage}
            onClose={handleCloseSession}
          />
        ) : (
          // Escalations Grid
          <div className="escalations-container">
            <div className="escalations-header">
              <h2>Active Escalations</h2>
              <span className="escalation-count">
                {escalations.length} {escalations.length === 1 ? 'conversation' : 'conversations'} waiting
              </span>
            </div>
            
            {escalations.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">✨</div>
                <h3>All caught up!</h3>
                <p>No escalations at the moment. New ones will appear here automatically.</p>
              </div>
            ) : (
              <div className="escalations-grid">
                {escalations.map(escalation => (
                  <EscalationCard
                    key={escalation.session_id}
                    escalation={escalation}
                    onTakeover={handleTakeover}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App