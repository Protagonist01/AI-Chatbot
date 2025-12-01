import React from 'react'

function ConnectionStatus({ status }) {
  const statusConfig = {
    connected: {
      label: 'Connected',
      color: '#10b981',
      icon: '●'
    },
    disconnected: {
      label: 'Disconnected',
      color: '#ef4444',
      icon: '●'
    },
    error: {
      label: 'Connection Error',
      color: '#f59e0b',
      icon: '●'
    }
  }

  const config = statusConfig[status] || statusConfig.disconnected

  return (
    <div className="connection-status">
      <span 
        className="status-indicator" 
        style={{ color: config.color }}
      >
        {config.icon}
      </span>
      <span className="status-label">{config.label}</span>
    </div>
  )
}

export default ConnectionStatus