import React from 'react'

function RealtimeStats({ metrics }) {
  const stats = [
    {
      label: 'Active Sessions',
      value: metrics.active_sessions || 0,
      icon: '🔄',
      color: '#3b82f6'
    },
    {
      label: 'Messages (Last Hour)',
      value: metrics.messages_last_hour || 0,
      icon: '💬',
      color: '#8b5cf6'
    },
    {
      label: 'Pending Escalations',
      value: metrics.escalations_pending || 0,
      icon: '🚨',
      color: '#ef4444'
    },
    {
      label: 'Agents Online',
      value: metrics.agents_online || 0,
      icon: '👥',
      color: '#10b981'
    },
    {
      label: 'Avg Response Time',
      value: metrics.avg_response_time_ms 
        ? `${(metrics.avg_response_time_ms / 1000).toFixed(1)}s`
        : 'N/A',
      icon: '⚡',
      color: '#f59e0b'
    }
  ]

  return (
    <div className="realtime-stats">
      <div className="stats-container">
        {stats.map((stat, index) => (
          <div key={index} className="stat-card">
            <div className="stat-icon" style={{ color: stat.color }}>
              {stat.icon}
            </div>
            <div className="stat-content">
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default RealtimeStats