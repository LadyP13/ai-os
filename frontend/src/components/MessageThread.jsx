import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { getMessages } from '../api.js'

export default function MessageThread({ user, wsConnected, sendWsMessage, newMessage }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  const fetchMessages = async () => {
    try {
      const res = await getMessages(100)
      setMessages(res.data)
    } catch (err) {
      // silently fail
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMessages()
  }, [])

  // Add new message from WebSocket
  useEffect(() => {
    if (newMessage) {
      setMessages((prev) => {
        // Avoid duplicates
        if (prev.find((m) => m.id === newMessage.id)) return prev
        return [...prev, newMessage]
      })
    }
  }, [newMessage])

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const content = input.trim()
    if (!content || sending) return

    setInput('')
    setSending(true)

    try {
      // Send via WebSocket for real-time
      sendWsMessage({ type: 'send_message', content })
    } catch (err) {
      console.error('Failed to send message:', err)
      setInput(content) // restore input on failure
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatTime = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatDate = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(today.getDate() - 1)

    if (d.toDateString() === today.toDateString()) return 'Today'
    if (d.toDateString() === yesterday.toDateString()) return 'Yesterday'
    return d.toLocaleDateString()
  }

  // Group messages by date
  const grouped = []
  let lastDate = null
  for (const msg of messages) {
    const dateLabel = formatDate(msg.created_at)
    if (dateLabel !== lastDate) {
      grouped.push({ type: 'date', label: dateLabel })
      lastDate = dateLabel
    }
    grouped.push({ type: 'message', data: msg })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h2 className="font-semibold text-text-primary">Messages</h2>
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-success' : 'bg-muted'}`}
          />
          <span className="text-xs text-text-secondary">
            {wsConnected ? 'Live' : 'Reconnecting...'}
          </span>
        </div>
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse flex gap-3">
                <div className="w-8 h-8 bg-border rounded-full flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-border rounded w-24" />
                  <div className="h-4 bg-border rounded w-3/4" />
                </div>
              </div>
            ))}
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center text-text-secondary py-12">
            <div className="text-4xl mb-3">💬</div>
            <p>No messages yet. Say hello!</p>
          </div>
        ) : (
          grouped.map((item, idx) => {
            if (item.type === 'date') {
              return (
                <div
                  key={`date-${idx}`}
                  className="flex items-center gap-3 my-4"
                >
                  <div className="flex-1 h-px bg-border" />
                  <span className="text-xs text-muted">{item.label}</span>
                  <div className="flex-1 h-px bg-border" />
                </div>
              )
            }

            const msg = item.data
            const isSystem = msg.message_type === 'system'
            const isMe = msg.sender_name === user.username

            if (isSystem) {
              return (
                <div
                  key={msg.id}
                  className="text-center text-xs text-muted italic py-1"
                >
                  {msg.content}
                </div>
              )
            }

            return (
              <div
                key={msg.id}
                className={`flex gap-3 ${isMe ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${
                    msg.sender_role === 'agent'
                      ? 'bg-accent/20 text-accent'
                      : 'bg-blue-900/30 text-blue-300'
                  }`}
                >
                  {msg.sender_role === 'agent' ? '🌳' : '👤'}
                </div>

                {/* Bubble */}
                <div
                  className={`max-w-[75%] ${isMe ? 'items-end' : 'items-start'} flex flex-col gap-1`}
                >
                  <div className="flex items-center gap-2">
                    {!isMe && (
                      <span className="text-xs font-medium text-text-secondary">
                        {msg.sender_name}
                      </span>
                    )}
                    <span
                      className={
                        msg.sender_role === 'agent'
                          ? 'badge-agent'
                          : 'badge-human'
                      }
                    >
                      {msg.sender_role}
                    </span>
                    <span className="text-xs text-muted">
                      {formatTime(msg.created_at)}
                    </span>
                  </div>
                  <div
                    className={`px-3 py-2 rounded-2xl text-sm ${
                      isMe
                        ? 'bg-accent/30 text-text-primary rounded-tr-sm'
                        : msg.sender_role === 'agent'
                        ? 'bg-surface border border-accent/20 text-text-primary rounded-tl-sm'
                        : 'bg-surface border border-border text-text-primary rounded-tl-sm'
                    }`}
                  >
                    {msg.sender_role === 'agent' ? (
                      <div className="prose prose-sm prose-invert max-w-none">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-border">
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            className="input resize-none h-10 py-2 flex-1"
            placeholder="Type a message... (Enter to send)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button
            className="btn-primary px-4 flex-shrink-0"
            onClick={handleSend}
            disabled={!input.trim() || sending}
          >
            {sending ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}
