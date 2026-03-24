import { useState, useEffect } from 'react'
import { listAgents, startAgent, stopAgent } from '../api.js'

export default function AgentStatus({ user, onAgentUpdate }) {
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(null)

  const fetchAgents = async () => {
    try {
      const res = await listAgents()
      setAgents(res.data)
      onAgentUpdate?.(res.data)
    } catch (err) {
      // silently fail
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAgents()
    const interval = setInterval(fetchAgents, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleToggle = async (agent) => {
    setActionLoading(agent.id)
    try {
      if (agent.status === 'running') {
        await stopAgent(agent.id)
      } else {
        await startAgent(agent.id)
      }
      await fetchAgents()
    } catch (err) {
      console.error('Failed to toggle agent:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const formatLastSeen = (lastSeen) => {
    if (!lastSeen) return 'Never'
    const date = new Date(lastSeen)
    const now = new Date()
    const diff = Math.floor((now - date) / 1000)

    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return date.toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="card h-full">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-border rounded w-3/4" />
          <div className="h-4 bg-border rounded w-1/2" />
        </div>
      </div>
    )
  }

  if (agents.length === 0) {
    return (
      <div className="card">
        <p className="text-text-secondary text-sm text-center py-4">
          No agents configured
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {agents.map((agent) => (
        <div key={agent.id} className="card">
          {/* Avatar + Name */}
          <div className="flex items-center gap-3 mb-3">
            <div className="text-3xl">🌳</div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-text-primary truncate">
                {agent.name}
              </h3>
              <span
                className={
                  agent.status === 'running'
                    ? 'status-running inline-block'
                    : 'status-stopped inline-block'
                }
              >
                {agent.status === 'running' ? '● running' : '○ stopped'}
              </span>
            </div>
          </div>

          {/* Last seen */}
          <div className="text-xs text-text-secondary mb-4">
            <span className="text-muted">Last seen: </span>
            {formatLastSeen(agent.last_seen)}
          </div>

          {/* Start/Stop button (human only) */}
          {user.role === 'human' && (
            <button
              className={
                agent.status === 'running' ? 'btn-danger w-full text-sm' : 'btn-success w-full text-sm'
              }
              onClick={() => handleToggle(agent)}
              disabled={actionLoading === agent.id}
            >
              {actionLoading === agent.id
                ? '...'
                : agent.status === 'running'
                ? '⏹ Stop Agent'
                : '▶ Start Agent'}
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
