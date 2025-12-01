import React from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

function CostAnalytics({ costSummary, detailed = false }) {
  if (!costSummary) {
    return (
      <div className="cost-analytics">
        <div className="loading-placeholder">Loading cost data...</div>
      </div>
    )
  }

  const { total_cost, cost_by_service, daily_costs, period_days } = costSummary

  // Prepare data for service breakdown pie chart
  const serviceData = Object.entries(cost_by_service || {}).map(([service, cost]) => ({
    name: service.replace('openai_', '').replace('_', ' '),
    value: parseFloat(cost),
    displayValue: `$${parseFloat(cost).toFixed(4)}`
  }))

  const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444']

  // Prepare data for daily cost trend
  const dailyData = (daily_costs || []).map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    cost: parseFloat(item.cost)
  }))

  return (
    <div className="cost-analytics">
      <div className="section-header">
        <h2>💰 Cost Analytics</h2>
        <div className="cost-summary">
          <span className="total-cost">${total_cost?.toFixed(2) || '0.00'}</span>
          <span className="cost-period">Last {period_days} days</span>
        </div>
      </div>

      {detailed ? (
        <>
          {/* Daily Cost Trend */}
          <div className="chart-container">
            <h3>Daily Cost Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="date" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                />
                <Tooltip 
                  formatter={(value) => [`$${value.toFixed(4)}`, 'Cost']}
                  contentStyle={{ 
                    background: 'white', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="cost" 
                  stroke="#3b82f6" 
                  strokeWidth={3}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Service Breakdown */}
          <div className="chart-grid">
            <div className="chart-container">
              <h3>Cost by Service</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={serviceData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.displayValue}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {serviceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `$${value.toFixed(4)}`} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-container">
              <h3>Service Breakdown</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={serviceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="name" 
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                  />
                  <YAxis 
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                    tickFormatter={(value) => `$${value.toFixed(3)}`}
                  />
                  <Tooltip formatter={(value) => [`$${value.toFixed(4)}`, 'Cost']} />
                  <Bar dataKey="value" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Cost Breakdown Table */}
          <div className="cost-table">
            <h3>Detailed Breakdown</h3>
            <table>
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Cost</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {serviceData.map((service, index) => (
                  <tr key={index}>
                    <td className="service-name">{service.name}</td>
                    <td className="service-cost">${service.value.toFixed(4)}</td>
                    <td className="service-percentage">
                      {((service.value / total_cost) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td><strong>Total</strong></td>
                  <td><strong>${total_cost?.toFixed(4)}</strong></td>
                  <td><strong>100%</strong></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </>
      ) : (
        // Compact view for overview tab
        <div className="cost-compact">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280"
                style={{ fontSize: '11px' }}
              />
              <YAxis 
                stroke="#6b7280"
                style={{ fontSize: '11px' }}
                tickFormatter={(value) => `$${value.toFixed(1)}`}
              />
              <Tooltip formatter={(value) => [`$${value.toFixed(4)}`, 'Cost']} />
              <Line 
                type="monotone" 
                dataKey="cost" 
                stroke="#8b5cf6" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

export default CostAnalytics