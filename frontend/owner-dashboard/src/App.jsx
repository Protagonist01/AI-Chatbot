import React, { useState, useEffect } from 'react'
import MetricsOverview from './components/MetricsOverview'
import RealtimeStats from './components/RealtimeStats'
import CostAnalytics from './components/CostAnalytics'
import CategoryPerformance from './components/CategoryPerformance'
import ConversationList from './components/ConversationList'
import DateRangePicker from './components/DateRangePicker'

const API_BASE = import.meta.env.VITE_API_BASE_URL

function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [dateRange, setDateRange] = useState(7) // days
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Data states
  const [realtimeMetrics, setRealtimeMetrics] = useState(null)
  const [dailyStats, setDailyStats] = useState(null)
  const [costSummary, setCostSummary] = useState(null)
  const [categoryStats, setCategoryStats] = useState([])
  const [conversations, setConversations] = useState([])

  // Fetch realtime metrics
  const fetchRealtimeMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/realtime`)
      if (!response.ok) throw new Error('Failed to fetch realtime metrics')
      const data = await response.json()
      setRealtimeMetrics(data)
    } catch (err) {
      console.error('Error fetching realtime metrics:', err)
    }
  }

  // Fetch daily stats
  const fetchDailyStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/daily`)
      if (!response.ok) throw new Error('Failed to fetch daily stats')
      const data = await response.json()
      setDailyStats(data)
    } catch (err) {
      console.error('Error fetching daily stats:', err)
      setError('Failed to load daily statistics')
    }
  }

  // Fetch cost summary
  const fetchCostSummary = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/dashboard/costs/summary?days=${dateRange}`
      )
      if (!response.ok) throw new Error('Failed to fetch cost summary')
      const data = await response.json()
      setCostSummary(data)
    } catch (err) {
      console.error('Error fetching cost summary:', err)
    }
  }

  // Fetch category stats
  const fetchCategoryStats = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/dashboard/categories?days=${dateRange}`
      )
      if (!response.ok) throw new Error('Failed to fetch category stats')
      const data = await response.json()
      setCategoryStats(data)
    } catch (err) {
      console.error('Error fetching category stats:', err)
    }
  }

  // Fetch conversations
  const fetchConversations = async (limit = 50) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/dashboard/conversations?limit=${limit}`
      )
      if (!response.ok) throw new Error('Failed to fetch conversations')
      const data = await response.json()
      setConversations(data.conversations || [])
    } catch (err) {
      console.error('Error fetching conversations:', err)
    }
  }

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      setError(null)
      
      try {
        await Promise.all([
          fetchRealtimeMetrics(),
          fetchDailyStats(),
          fetchCostSummary(),
          fetchCategoryStats(),
          fetchConversations()
        ])
      } catch (err) {
        setError('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  // Refresh data when date range changes
  useEffect(() => {
    fetchCostSummary()
    fetchCategoryStats()
  }, [dateRange])

  // Auto-refresh realtime metrics every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchRealtimeMetrics()
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'costs', label: 'Costs', icon: '💰' },
    { id: 'categories', label: 'Categories', icon: '📂' },
    { id: 'conversations', label: 'Conversations', icon: '💬' }
  ]

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <h1>📊 Owner Dashboard</h1>
            <p className="header-subtitle">AI Support Platform Analytics</p>
          </div>
          <div className="header-right">
            <DateRangePicker value={dateRange} onChange={setDateRange} />
            <button 
              onClick={() => window.location.reload()} 
              className="btn-refresh"
              title="Refresh Dashboard"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Realtime Stats Bar */}
      {realtimeMetrics && (
        <RealtimeStats metrics={realtimeMetrics} />
      )}

      {/* Navigation Tabs */}
      <nav className="dashboard-nav">
        <div className="nav-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="dashboard-content">
        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading dashboard data...</p>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <div className="tab-content">
                <MetricsOverview 
                  dailyStats={dailyStats}
                  realtimeMetrics={realtimeMetrics}
                />
                
                <div className="content-grid">
                  <div className="grid-item">
                    <CostAnalytics costSummary={costSummary} />
                  </div>
                  <div className="grid-item">
                    <CategoryPerformance 
                      categoryStats={categoryStats}
                      compact={true}
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'costs' && (
              <div className="tab-content">
                <CostAnalytics costSummary={costSummary} detailed={true} />
              </div>
            )}

            {activeTab === 'categories' && (
              <div className="tab-content">
                <CategoryPerformance categoryStats={categoryStats} />
              </div>
            )}

            {activeTab === 'conversations' && (
              <div className="tab-content">
                <ConversationList conversations={conversations} />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App