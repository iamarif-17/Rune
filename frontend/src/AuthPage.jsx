import { useState, useEffect, useRef } from 'react'
import './AuthPage.css'

// Paste the Client ID from Google Cloud Console (APIs & Services > Credentials)
const GOOGLE_CLIENT_ID = '954452848625-v9trdq0okep1ikef5525rnud9n2baos5.apps.googleusercontent.com'

// Your FastAPI backend — change the port here if uvicorn is running on a different one
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function AuthPage({ mode: initialMode = 'login', onAuthed, onBack }) {
  const [mode, setMode] = useState(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const googleBtnRef = useRef(null)

  useEffect(() => {
    if (GOOGLE_CLIENT_ID.startsWith('YOUR_GOOGLE_CLIENT_ID')) return

    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleCredential,
      })
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        theme: 'outline',
        size: 'large',
        width: 320,
        text: mode === 'login' ? 'signin_with' : 'signup_with',
      })
    }
    document.body.appendChild(script)
    return () => { document.body.removeChild(script) }
  }, [mode])

  async function handleGoogleCredential(response) {
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: response.credential }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Google sign-in failed. Try again.')
      }
      const data = await res.json()
      localStorage.setItem('rune_token', data.access_token)
      if (data.email) localStorage.setItem('rune_username', data.email)
      onAuthed(data.access_token)
    } catch (err) {
      setError(err.message || 'Could not reach the server.')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Something went wrong. Try again.')
      }
      const data = await res.json()
      localStorage.setItem('rune_token', data.access_token)
      localStorage.setItem('rune_username', email)
      onAuthed(data.access_token)
    } catch (err) {
      setError(err.message || 'Could not reach the server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <button className="auth-back-btn" onClick={onBack}>← Back</button>

      <div className="auth-card">
        <div className="auth-logo">
          <img src="/Rune.png" alt="Rune logo" width="20" height="20" style={{ objectFit: 'contain', borderRadius: 4 }} />
          <span>Rune</span>
        </div>

        <h1 className="auth-title">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
        <p className="auth-subtitle">
          {mode === 'login' ? 'Log in to keep researching.' : 'Sign up to start using Rune.'}
        </p>

        <div ref={googleBtnRef} className="auth-google-btn" />

        {!GOOGLE_CLIENT_ID.startsWith('YOUR_GOOGLE_CLIENT_ID') && (
          <div className="auth-divider"><span>OR</span></div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </label>

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Log in' : 'Sign up'}
          </button>
        </form>

        <p className="auth-switch">
          {mode === 'login' ? (
            <>Don't have an account?{' '}
              <button onClick={() => setMode('signup')}>Sign up</button>
            </>
          ) : (
            <>Already have an account?{' '}
              <button onClick={() => setMode('login')}>Log in</button>
            </>
          )}
        </p>
      </div>
    </div>
  )
}