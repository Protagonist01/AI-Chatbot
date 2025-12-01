import React from 'react'

function MetricsOverview({ dailyStats, realtimeMetrics }) {
  if (!dailyStats) {
    return (
      <div className="metrics-overview">
        <div className="loading-placeholder">Loading metrics...</div>
      </div>
    )
  }

  const metrics = [
    {
      title: 'Total Conversations',
      value: dailyStats.total_conversations || 0,
      subtitle: 'Today',
      icon: '💬',
      color: '#3b82f6'
    },
    {
      title: 'AI Resolved',
      value: dailyStats.ai_resolved || 0,
      subtitle: `${dailyStats.ai_resolution_rate?.toFixed(1) || 0}% success rate`,
      icon: '🤖',
      color: '#10b981'
    },
    {
      title: 'Human Escalations',
      value: dailyStats.human_escalations || 0,
      subtitle: `${(100 - (dailyStats.ai_resolution_rate || 0)).toFixed(1)}% escalated`,
      icon: '👤',
      color: '#f59e0b'
    },
    {
      title: 'Total Cost',
      value: `$${dailyStats.total_cost_usd?.toFixed(2) || '0.00'}`,
      subtitle: `$${dailyStats.avg_cost_per_conversation?.toFixed(4) || '0.0000'} per conversation`,
      icon: '💰',
      color: '#8b5cf6'
    }
  ]

  return (
    <div className="metrics-overview">
      <div className="metrics-grid">
        {metrics.map((metric, index) => (
          <div key={index} className="metric-card">
            <div className="metric-header">
              <span className="metric-icon" style={{ color: metric.color }}>
                {metric.icon}
              </span>
              <span className="metric-title">{metric.title}</span>
            </div>
            <div className="metric-value">{metric.value}</div>
            <div className="metric-subtitle">{metric.subtitle}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default MetricsOverview