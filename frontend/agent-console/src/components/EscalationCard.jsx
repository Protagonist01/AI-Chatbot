import React from 'react'

function EscalationCard({ escalation, onTakeover }) {
  const channelIcons = {
    whatsapp: '💬',
    telegram: '✈️',
    web: '🌐'
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = Math.floor((now - date) / 1000 / 60) // minutes

    if (diff < 1) return 'Just now'
    if (diff < 60) return `${diff}m ago`
    if (diff < 1440) return `${Math.floor(diff / 60)}h ago`
    return date.toLocaleString()
  }

  const recentMessages = escalation.recent_messages || []
  const lastUserMessage = recentMessages
    .filter(m => m.sender === 'user')
    .slice(-1)[0]

  return (
    <div className="escalation-card">
      <div className="card-header">
        <div className="card-channel">
          <span className="channel-icon">
            {channelIcons[escalation.channel] || '📱'}
          </span>
          <span className="channel-name">{escalation.channel}</span>
        </div>
        <span className="card-time">{formatTime(escalation.escalated_at)}</span>
      </div>

      <div className="card-body">
        <div className="card-category">
          <span className="category-badge">{escalation.category}</span>
        </div>

        {escalation.reason && (
          <div className="card-reason">
            <strong>Reason:</strong> {escalation.reason}
          </div>
        )}

        {lastUserMessage && (
          <div className="card-last-message">
            <strong>Last message:</strong>
            <p>{lastUserMessage.content}</p>
          </div>
        )}

        {escalation.conversation_summary && (
          <div className="card-summary">
            <strong>Summary:</strong>
            <p>{escalation.conversation_summary}</p>
          </div>
        )}
      </div>

      <div className="card-footer">
        <button
          onClick={() => onTakeover(escalation.session_id)}
          className="btn-takeover"
        >
          Take Over Conversation
        </button>
      </div>
    </div>
  )
}

export default EscalationCard