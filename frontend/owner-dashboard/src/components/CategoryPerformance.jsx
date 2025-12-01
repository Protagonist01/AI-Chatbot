import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'

function CategoryPerformance({ categoryStats, compact = false }) {
  if (!categoryStats || categoryStats.length === 0) {
    return (
      <div className="category-performance">
        <div className="loading-placeholder">No category data available</div>
      </div>
    )
  }

  const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4']

  return (
    <div className="category-performance">
      <div className="section-header">
        <h2>📂 Category Performance</h2>
      </div>

      {!compact && (
        <div className="chart-container">
          <h3>Messages by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categoryStats}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="category" 
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip />
              <Bar dataKey="total_messages" fill="#3b82f6" radius={[8, 8, 0, 0]}>
                {categoryStats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="category-table">
        <table>
          <thead>
            <tr>
              <th>Category</th>
              <th>Messages</th>
              <th>AI Success Rate</th>
              <th>Total Cost</th>
              <th>Avg Cost/Msg</th>
            </tr>
          </thead>
          <tbody>
            {categoryStats.map((cat, index) => (
              <tr key={index}>
                <td className="category-name">
                  <span 
                    className="category-badge"
                    style={{ background: `${COLORS[index % COLORS.length]}20`, color: COLORS[index % COLORS.length] }}
                  >
                    {cat.category}
                  </span>
                </td>
                <td>{cat.total_messages}</td>
                <td>
                  <div className="progress-cell">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${cat.ai_resolved_pct}%`, background: COLORS[index % COLORS.length] }}
                      />
                    </div>
                    <span className="progress-label">{cat.ai_resolved_pct.toFixed(1)}%</span>
                  </div>
                </td>
                <td>${cat.total_cost_usd.toFixed(4)}</td>
                <td>${(cat.total_cost_usd / cat.total_messages).toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default CategoryPerformance