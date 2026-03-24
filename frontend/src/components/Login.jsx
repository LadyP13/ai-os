import { useState } from 'react'
import { login } from '../api.js'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [totpCode, setTotpCode] = useState('')
  const [requires2FA, setRequires2FA] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await login(
        username,
        password,
        requires2FA ? totpCode : null
      )
      const data = res.data

      if (data.requires_2fa && !data.access_token) {
        setRequires2FA(true)
        setLoading(false)
        return
      }

      if (data.access_token) {
        onLogin(
          {
            username: data.username,
            role: data.role,
          },
          data.access_token
        )
      }
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        'Login failed. Check your credentials.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🌳</div>
          <h1 className="text-3xl font-bold text-accent">AI-OS</h1>
          <p className="text-text-secondary mt-2">Agent Operating System</p>
        </div>

        {/* Login Card */}
        <div className="card">
          <h2 className="text-xl font-semibold text-text-primary mb-6">
            {requires2FA ? 'Two-Factor Authentication' : 'Sign In'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!requires2FA ? (
              <>
                <div>
                  <label className="block text-sm text-text-secondary mb-1">
                    Username
                  </label>
                  <input
                    type="text"
                    className="input"
                    placeholder="your-username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    autoFocus
                    autoComplete="username"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-text-secondary mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    className="input"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    required
                  />
                </div>
              </>
            ) : (
              <div>
                <p className="text-text-secondary text-sm mb-4">
                  Enter the 6-digit code from your authenticator app.
                </p>
                <label className="block text-sm text-text-secondary mb-1">
                  Authentication Code
                </label>
                <input
                  type="text"
                  className="input text-center text-xl tracking-widest"
                  placeholder="000000"
                  value={totpCode}
                  onChange={(e) =>
                    setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                  }
                  maxLength={6}
                  autoFocus
                  required
                />
              </div>
            )}

            {error && (
              <div className="bg-danger/10 border border-danger/30 text-danger text-sm px-3 py-2 rounded-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn-primary w-full"
              disabled={loading}
            >
              {loading
                ? 'Signing in...'
                : requires2FA
                ? 'Verify Code'
                : 'Sign In'}
            </button>

            {requires2FA && (
              <button
                type="button"
                className="btn-secondary w-full text-sm"
                onClick={() => {
                  setRequires2FA(false)
                  setTotpCode('')
                  setError('')
                }}
              >
                Back
              </button>
            )}
          </form>
        </div>

        <p className="text-center text-text-secondary text-xs mt-6">
          AI-OS — Local deployment
        </p>
      </div>
    </div>
  )
}
