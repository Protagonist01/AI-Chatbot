import React, { useState } from 'react'

function ConversationList({ conversations }) {
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [filter, setFilter] = useState('all') // all, active, escalated, resolved

  const filteredConversations = conversations.filter(conv => {
    if (filter === 'all') return true
    return conv.status === filter
  })

  const statusBadgeColors = {
    active: '#3b82f6',
    escalated: '#f59e0b',
    resolved: '#10b981',
    closed: '#6b7280'
  }

  const channelIcons = {
    whatsapp: '💬',
    telegram: '✈️',
    web: '🌐'
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="conversation-list">
      <div className="section-header">
        <h2>💬 Recent Conversations</h2>
        <div className="conversation-filters">
          {['all', 'active', 'escalated', 'resolved'].map(status => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`filter-btn ${filter === status ? 'active' : ''}`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="conversations-container">
        <table className="conversations-table">
          <thead>
            <tr>
              <th>Channel</th>
              <th>Category</th>
              <th>Status</th>
              <th>Started</th>
              <th>Messages</th>
              <th>Agent</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredConversations.map((conv) => (
              <tr key={conv.id} className="conversation-row">
                <td>
                  <span className="channel-cell">
                    <span className="channel-icon">{channelIcons[conv.channel] || '📱'}</span>
                    {conv.channel}
                  </span>
                </td>
                <td>
                  {conv.selected_category ? (
                    <span className="category-badge-small">{conv.selected_category}</span>
                  ) : (
                    <span className="text-muted">-</span>
                  )}
                </td>
                <td>
                  <span 
                    className="status-badge"
                    style={{ 
                      background: `${statusBadgeColors[conv.status]}20`,
                      color: statusBadgeColors[conv.status]
                    }}
                  >
                    {conv.status}
                  </span>
                </td>
                <td className="date-cell">{formatDate(conv.created_at)}</td>
                <td className="text-center">
                  {conv.events?.length || 0}
                </td>
                <td>
                  {conv.assigned_agent_id ? (
                    <span className="agent-name">{conv.assigned_agent_id}</span>
                  ) : (
                    <span className="text-muted">AI Only</span>
                  )}
                </td>
                <td>
                  <button 
                    onClick={() => setSelectedConversation(conv)}
                    className="btn-view-small"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredConversations.length === 0 && (
          <div className="empty-conversations">
            <p>No {filter !== 'all' ? filter : ''} conversations found</p>
          </div>
        )}
      </div>

      {/* Conversation Detail Modal */}
      {selectedConversation && (
        <div className="modal-overlay" onClick={() => setSelectedConversation(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Conversation Details</h3>
              <button 
                onClick={() => setSelectedConversation(null)}
                className="btn-close-modal"
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="conversation-meta">
                <div className="meta-item">
                  <strong>Session ID:</strong> {selectedConversation.id}
                </div>
                <div className="meta-item">
                  <strong>Channel:</strong> {selectedConversation.channel}
                </div>
                <div className="meta-item">
                  <strong>Category:</strong> {selectedConversation.selected_category || 'Not selected'}
                </div>
                <div className="meta-item">
                  <strong>Status:</strong> {selectedConversation.status}
                </div>
                <div className="meta-item">
                  <strong>Created:</strong> {formatDate(selectedConversation.created_at)}
                </div>
                {selectedConversation.assigned_agent_id && (
                  <div className="meta-item">
                    <strong>Agent:</strong> {selectedConversation.assigned_agent_id}
                  </div>
                )}
              </div>

              <div className="conversation-events">
                <h4>Message History</h4>
                <div className="events-list">
                  {selectedConversation.events?.map((event, index) => (
                    <div key={index} className={`event-item event-${event.sender}`}>
                      <div className="event-header">
                        <span className="event-sender">{event.sender}</span>
                        <span className="event-time">{formatDate(event.created_at)}</span>
                      </div>
                      <div className="event-content">{event.content}</div>
                    </div>
                  )) || <p className="text-muted">No messages loaded</p>}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ConversationList