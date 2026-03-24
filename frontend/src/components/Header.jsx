import { useState } from 'react'
import { setup2FA, verify2FA } from '../api.js'

export default function Header({ user, onLogout }) {
  const [show2FAModal, setShow2FAModal] = useState(false)
  const [qrCode, setQrCode] = useState(null)
  const [secret, setSecret] = useState(null)
  const [verifyCode, setVerifyCode] = useState('')
  const [step, setStep] = useState('setup') // 'setup' | 'verify' | 'done'
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const open2FASetup = async () => {
    setError('')
    setStep('setup')
    setShow2FAModal(true)
    setLoading(true)
    try {
      const res = await setup2FA()
      setQrCode(res.data.qr_code)
      setSecret(res.data.secret)
      setStep('verify')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to setup 2FA')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async () => {
    if (!verifyCode.trim()) return
    setLoading(true)
    setError('')
    try {
      await verify2FA(verifyCode)
      setStep('done')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid code')
    } finally {
      setLoading(false)
    }
  }

  const closeModal = () => {
    setShow2FAModal(false)
    setQrCode(null)
    setSecret(null)
    setVerifyCode('')
    setStep('setup')
    setError('')
  }

  return (
    <>
      <header className="bg-surface border-b border-border px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <span className="text-xl">🌳</span>
          <span className="font-bold text-accent text-lg">AI-OS</span>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          <div className="text-sm text-text-secondary hidden sm:block">
            <span className="text-text-primary font-medium">{user.username}</span>
            <span
              className={`ml-2 ${user.role === 'human' ? 'badge-human' : 'badge-agent'}`}
            >
              {user.role}
            </span>
          </div>

          {/* 2FA button (human only) */}
          {user.role === 'human' && (
            <button
              className="text-text-secondary hover:text-accent transition-colors"
              title="Security Settings"
              onClick={open2FASetup}
            >
              ⚙️
            </button>
          )}

          {/* Logout */}
          <button
            className="btn-secondary text-sm py-1.5 px-3"
            onClick={onLogout}
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* 2FA Setup Modal */}
      {show2FAModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-text-primary">
                Two-Factor Authentication
              </h2>
              <button
                className="text-muted hover:text-text-primary text-xl leading-none"
                onClick={closeModal}
              >
                ×
              </button>
            </div>

            {loading && step === 'setup' && (
              <div className="text-center py-8 text-text-secondary animate-pulse">
                Setting up 2FA...
              </div>
            )}

            {step === 'verify' && qrCode && (
              <div className="space-y-4">
                <p className="text-sm text-text-secondary">
                  Scan this QR code with your authenticator app (Google
                  Authenticator, Authy, etc.):
                </p>

                <div className="flex justify-center">
                  <img
                    src={`data:image/png;base64,${qrCode}`}
                    alt="2FA QR Code"
                    className="w-48 h-48 rounded-lg"
                  />
                </div>

                <div className="bg-bg border border-border rounded-lg p-3">
                  <p className="text-xs text-muted mb-1">
                    Or enter manually:
                  </p>
                  <code className="text-xs text-success font-mono break-all">
                    {secret}
                  </code>
                </div>

                <div>
                  <label className="block text-sm text-text-secondary mb-1">
                    Verify with code from your app:
                  </label>
                  <input
                    type="text"
                    className="input text-center text-xl tracking-widest"
                    placeholder="000000"
                    value={verifyCode}
                    onChange={(e) =>
                      setVerifyCode(
                        e.target.value.replace(/\D/g, '').slice(0, 6)
                      )
                    }
                    maxLength={6}
                    autoFocus
                  />
                </div>

                {error && (
                  <div className="bg-danger/10 border border-danger/30 text-danger text-sm px-3 py-2 rounded-lg">
                    {error}
                  </div>
                )}

                <button
                  className="btn-primary w-full"
                  onClick={handleVerify}
                  disabled={verifyCode.length !== 6 || loading}
                >
                  {loading ? 'Verifying...' : 'Enable 2FA'}
                </button>
              </div>
            )}

            {step === 'done' && (
              <div className="text-center py-6">
                <div className="text-5xl mb-4">✅</div>
                <h3 className="text-lg font-semibold text-success mb-2">
                  2FA Enabled!
                </h3>
                <p className="text-text-secondary text-sm mb-4">
                  Your account is now protected with two-factor authentication.
                  You'll need your authenticator app every time you sign in.
                </p>
                <button className="btn-primary" onClick={closeModal}>
                  Done
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
