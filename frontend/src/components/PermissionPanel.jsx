import { useState, useEffect } from 'react'
import { listAgents, getPermissions, togglePermission } from '../api.js'

const DANGEROUS_PERMISSIONS = ['filesystem_delete', 'git_push']

export default function PermissionPanel({ user }) {
  const [agents, setAgents] = useState([])
  const [selectedAgentId, setSelectedAgentId] = useState(null)
  const [permissions, setPermissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState(null)
  const [confirmDanger, setConfirmDanger] = useState(null)

  useEffect(() => {
    listAgents()
      .then((res) => {
        setAgents(res.data)
        if (res.data.length > 0) {
          setSelectedAgentId(res.data[0].id)
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedAgentId) return
    setLoading(true)
    getPermissions(selectedAgentId)
      .then((res) => setPermissions(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [selectedAgentId])

  const handleToggle = async (perm, newValue) => {
    if (user.role !== 'human') return

    // Confirm dangerous permissions being enabled
    if (newValue && DANGEROUS_PERMISSIONS.includes(perm.permission_key)) {
      setConfirmDanger({ perm, newValue })
      return
    }

    await doToggle(perm, newValue)
  }

  const doToggle = async (perm, newValue) => {
    setToggling(perm.permission_key)
    try {
      const res = await togglePermission(selectedAgentId, perm.permission_key, newValue)
      setPermissions((prev) =>
        prev.map((p) =>
          p.permission_key === perm.permission_key
            ? { ...p, enabled: res.data.enabled }
            : p
        )
      )
    } catch (err) {
      console.error('Failed to toggle permission:', err)
    } finally {
      setToggling(null)
    }
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card animate-pulse">
            <div className="h-4 bg-border rounded w-3/4 mb-1" />
            <div className="h-3 bg-border rounded w-1/2" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div>
      {/* Agent selector */}
      {agents.length > 1 && (
        <div className="mb-4">
          <select
            className="input text-sm"
            value={selectedAgentId || ''}
            onChange={(e) => setSelectedAgentId(Number(e.target.value))}
          >
            {agents.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {user.role !== 'human' && (
        <div className="bg-muted/10 border border-muted/20 text-muted text-xs px-3 py-2 rounded-lg mb-4">
          Only human accounts can modify permissions.
        </div>
      )}

      {/* Permission grid */}
      <div className="space-y-2">
        {permissions.map((perm) => {
          const isDangerous = DANGEROUS_PERMISSIONS.includes(perm.permission_key)
          return (
            <div
              key={perm.permission_key}
              className={`card flex items-center gap-3 py-3 ${
                isDangerous && perm.enabled ? 'border-warning/40' : ''
              }`}
            >
              <span className="text-xl flex-shrink-0">{perm.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-text-primary">
                    {perm.label}
                  </span>
                  {isDangerous && (
                    <span className="text-xs text-warning">⚠️</span>
                  )}
                </div>
                <p className="text-xs text-text-secondary truncate">
                  {perm.description}
                </p>
              </div>

              {/* Toggle */}
              <button
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 transition-colors duration-200 focus:outline-none ${
                  perm.enabled
                    ? 'bg-success border-success'
                    : 'bg-border border-border'
                } ${user.role !== 'human' ? 'opacity-50 cursor-not-allowed' : ''} ${
                  toggling === perm.permission_key ? 'opacity-70' : ''
                }`}
                onClick={() =>
                  user.role === 'human' && handleToggle(perm, !perm.enabled)
                }
                disabled={toggling === perm.permission_key || user.role !== 'human'}
                title={perm.description}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200 mt-0.5 ${
                    perm.enabled ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
          )
        })}
      </div>

      {/* Dangerous confirmation modal */}
      {confirmDanger && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card max-w-sm w-full border-warning/40">
            <div className="text-xl mb-2">⚠️</div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              Enable {confirmDanger.perm.label}?
            </h3>
            <p className="text-sm text-text-secondary mb-4">
              {confirmDanger.perm.description}. This is a potentially dangerous
              permission. Are you sure?
            </p>
            <div className="flex gap-3">
              <button
                className="btn-danger flex-1"
                onClick={() => {
                  doToggle(confirmDanger.perm, confirmDanger.newValue)
                  setConfirmDanger(null)
                }}
              >
                Enable Anyway
              </button>
              <button
                className="btn-secondary flex-1"
                onClick={() => setConfirmDanger(null)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
