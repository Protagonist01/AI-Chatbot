import React, { useState, useEffect, useRef } from 'react'

function ChatInterface({ sessionId, messages, onSendMessage, onClose }) {
  const [messageText, setMessageText] = useState('')
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!messageText.trim()) return

    onSendMessage(messageText)
    setMessageText('')
  }

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getSenderLabel = (sender) => {
    switch (sender) {
      case 'user': return 'Customer'
      case 'bot': return 'AI Assistant'
      case 'agent': return 'You'
      case 'system': return 'System'
      default: return sender
    }
  }

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="chat-title">
          <h3>Conversation</h3>
          <span className="session-id">Session: {sessionId.slice(0, 8)}...</span>
        </div>
        <button onClick={onClose} className="btn-close-chat">
          ← Back to Escalations
        </button>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div
            key={msg.event_id}
            className={`message message-${msg.sender}`}
          >
            <div className="message-header">
              <span className="message-sender">{getSenderLabel(msg.sender)}</span>
              <span className="message-time">{formatTime(msg.created_at)}</span>
            </div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <textarea
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          placeholder="Type your message to the customer..."
          rows={3}
          className="chat-input"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSubmit(e)
            }
          }}
        />
        <button type="submit" className="btn-send" disabled={!messageText.trim()}>
          Send Message
        </button>
      </form>
    </div>
  )
}

export default ChatInterface