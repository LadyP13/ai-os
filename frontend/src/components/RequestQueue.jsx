import { useState, useEffect } from 'react'
import { getRequests, resolveRequest } from '../api.js'

export default function RequestQueue({ user, newRequest, resolvedRequest }) {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(null)

  const fetchRequests = async () => {
    try {
      const res = await getRequests()
      setRequests(res.data)
    } catch (err) {
      // silently fail
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  // Add new request from WebSocket
  useEffect(() => {
    if (newRequest) {
      setRequests((prev) => {
        if (prev.find((r) => r.id === newRequest.id)) return prev
        return [newRequest, ...prev]
      })
    }
  }, [newRequest])

  // Update resolved request from WebSocket
  useEffect(() => {
    if (resolvedRequest) {
      setRequests((prev) =>
        prev.map((r) =>
          r.id === resolvedRequest.request_id
            ? { ...r, status: resolvedRequest.status }
            : r
        )
      )
    }
  }, [resolvedRequest])

  const handleResolve = async (requestId, status) => {
    setActionLoading(`${requestId}-${status}`)
    try {
      await resolveRequest(requestId, status)
      setRequests((prev) =>
        prev.map((r) => (r.id === requestId ? { ...r, status } : r))
      )
    } catch (err) {
      console.error('Failed to resolve request:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const formatTime = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    return d.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const pending = requests.filter((r) => r.status === 'pending')
  const resolved = requests.filter((r) => r.status !== 'pending')

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <div key={i} className="card animate-pulse">
            <div className="h-4 bg-border rounded w-3/4 mb-2" />
            <div className="h-3 bg-border rounded w-1/2" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Pending requests */}
      {pending.length === 0 ? (
        <div className="text-center text-text-secondary text-sm py-6">
          <div className="text-3xl mb-2">✅</div>
          No pending requests
        </div>
      ) : (
        <div className="space-y-3">
          {pending.map((req) => (
            <div
              key={req.id}
              className="card border-warning/30 bg-warning/5"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <span className="bg-warning/20 text-warning text-xs px-2 py-0.5 rounded-full border border-warning/30">
                    {req.request_type}
                  </span>
                </div>
                <span className="text-xs text-muted flex-shrink-0">
                  {formatTime(req.created_at)}
                </span>
              </div>

              <p className="text-sm text-text-primary mb-1">
                {req.description}
              </p>

              {req.agent_name && (
                <p className="text-xs text-text-secondary mb-3">
                  From: {req.agent_name}
                </p>
              )}

              {req.detail_json && (
                <pre className="text-xs bg-bg border border-border rounded p-2 overflow-auto mb-3 text-text-secondary max-h-24">
                  {JSON.stringify(req.detail_json, null, 2)}
                </pre>
              )}

              {user.role === 'human' && (
                <div className="flex gap-2">
                  <button
                    className="btn-success flex-1 text-sm py-1"
                    onClick={() => handleResolve(req.id, 'approved')}
                    disabled={actionLoading !== null}
                  >
                    {actionLoading === `${req.id}-approved`
                      ? '...'
                      : '✅ Approve'}
                  </button>
                  <button
                    className="btn-danger flex-1 text-sm py-1"
                    onClick={() => handleResolve(req.id, 'denied')}
                    disabled={actionLoading !== null}
                  >
                    {actionLoading === `${req.id}-denied`
                      ? '...'
                      : '❌ Deny'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Resolved requests */}
      {resolved.length > 0 && (
        <div>
          <h3 className="text-xs text-muted uppercase tracking-wider mb-2">
            Recent Resolutions
          </h3>
          <div className="space-y-2">
            {resolved.slice(0, 5).map((req) => (
              <div key={req.id} className="card opacity-60 py-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs text-text-secondary mr-2">
                      {req.request_type}
                    </span>
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded-full ${
                        req.status === 'approved'
                          ? 'bg-success/20 text-success'
                          : 'bg-danger/20 text-danger'
                      }`}
                    >
                      {req.status}
                    </span>
                  </div>
                  <span className="text-xs text-muted">
                    {formatTime(req.created_at)}
                  </span>
                </div>
                <p className="text-xs text-text-secondary mt-1 truncate">
                  {req.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
