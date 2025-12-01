import React, { useState } from 'react'

function LoginScreen({ onLogin }) {
  const [token, setToken] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!token.trim()) {
      setError('Please enter a token')
      return
    }

    try {
      onLogin(token.trim())
    } catch (e) {
      setError('Invalid token format')
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🎧 Agent Console</h1>
          <p>AI Support Platform</p>
        </div>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="token">Agent Token</label>
            <textarea
              id="token"
              value={token}
              onChange={(e) => {
                setToken(e.target.value)
                setError('')
              }}
              placeholder="Paste your agent JWT token here..."
              rows={8}
              className="token-input"
            />
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button type="submit" className="btn-login">
            Sign In
          </button>
        </form>
        
        <div className="login-footer">
          <p>Contact your administrator for an agent token</p>
        </div>
      </div>
    </div>
  )
}

export default LoginScreen