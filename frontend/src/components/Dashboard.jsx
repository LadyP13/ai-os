import { useState, useCallback } from 'react'
import Header from './Header.jsx'
import AgentStatus from './AgentStatus.jsx'
import MessageThread from './MessageThread.jsx'
import RequestQueue from './RequestQueue.jsx'
import PermissionPanel from './PermissionPanel.jsx'
import useWebSocket from '../useWebSocket.js'

export default function Dashboard({ user, onLogout }) {
  const [rightTab, setRightTab] = useState('requests') // 'requests' | 'permissions'
  const [newMessage, setNewMessage] = useState(null)
  const [newRequest, setNewRequest] = useState(null)
  const [resolvedRequest, setResolvedRequest] = useState(null)
  const [pendingCount, setPendingCount] = useState(0)

  const handleWsMessage = useCallback((data) => {
    switch (data.type) {
      case 'new_message':
        setNewMessage(data.message)
        break
      case 'new_request':
        setNewRequest(data.request)
        setPendingCount((c) => c + 1)
        // Auto-switch to requests tab if not already there
        setRightTab('requests')
        break
      case 'request_resolved':
        setResolvedRequest({ request_id: data.request_id, status: data.status })
        setPendingCount((c) => Math.max(0, c - 1))
        break
      case 'agent_status':
        // AgentStatus component handles this via polling
        break
      default:
        break
    }
  }, [])

  const { connected, sendMessage: sendWsMessage } = useWebSocket(handleWsMessage)

  return (
    <div className="flex flex-col h-screen bg-bg overflow-hidden">
      <Header user={user} onLogout={onLogout} />

      <div className="flex flex-1 overflow-hidden">
        {/* Left column: Agent Status */}
        <aside className="w-56 flex-shrink-0 border-r border-border overflow-y-auto p-3">
          <h2 className="text-xs text-muted uppercase tracking-wider mb-3 px-1">
            Agents
          </h2>
          <AgentStatus user={user} />
        </aside>

        {/* Center column: Messages */}
        <main className="flex-1 flex flex-col overflow-hidden border-r border-border">
          <MessageThread
            user={user}
            wsConnected={connected}
            sendWsMessage={sendWsMessage}
            newMessage={newMessage}
          />
        </main>

        {/* Right column: Requests + Permissions */}
        <aside className="w-80 flex-shrink-0 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-border">
            <button
              className={`flex-1 py-3 text-sm font-medium transition-colors relative ${
                rightTab === 'requests'
                  ? 'text-accent border-b-2 border-accent -mb-px'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
              onClick={() => setRightTab('requests')}
            >
              Requests
              {pendingCount > 0 && (
                <span className="ml-2 bg-warning text-black text-xs font-bold px-1.5 py-0.5 rounded-full">
                  {pendingCount}
                </span>
              )}
            </button>
            <button
              className={`flex-1 py-3 text-sm font-medium transition-colors ${
                rightTab === 'permissions'
                  ? 'text-accent border-b-2 border-accent -mb-px'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
              onClick={() => setRightTab('permissions')}
            >
              Permissions
            </button>
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-3">
            {rightTab === 'requests' ? (
              <RequestQueue
                user={user}
                newRequest={newRequest}
                resolvedRequest={resolvedRequest}
              />
            ) : (
              <PermissionPanel user={user} />
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
