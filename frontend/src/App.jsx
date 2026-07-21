import { useState, useRef } from 'react'
import LandingPage from './LandingPage.jsx'
import AuthPage from './AuthPage.jsx'
import Sidebar from './components/Sidebar.jsx'
import ChatThread from './components/ChatThread.jsx'
import InputBar from './components/InputBar.jsx'
import SettingsModal from './components/SettingsModal.jsx'

const API_URL = import.meta.env.VITE_API_URL || ''

const GREETINGS = [
  'What should we look into?',
  'Where should we begin?',
  'What are we uncovering today?',
  "What's worth investigating?",
  'Bring me a question',
  'Name the topic',
  'What deserves a closer look?',
  "What's the inquiry?",
  'Curiosity, then clarity',
  "Let's dig into something",
  'What are we chasing today?',
  'Point me somewhere',
  'Ready to go find out',
  "What's on the docket?",
  'Something to investigate?',
]

function getGreeting() {
  const name = localStorage.getItem('rune_username')
  const hour = new Date().getHours()
  const timeOfDay = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening'
  if (name) return `Good ${timeOfDay}, ${name}`
  return GREETINGS[Math.floor(Math.random() * GREETINGS.length)]
}

const CONTENT_WIDTH = 860

export default function App() {
  const [screen, setScreen] = useState(() =>
    localStorage.getItem('rune_token') ? 'chat' : 'landing'
  )
  const [authMode, setAuthMode] = useState('login')
  const [pendingQuery, setPendingQuery] = useState(null)

  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [hoverToggle, setHoverToggle] = useState(false)
  const [greeting, setGreeting] = useState(getGreeting)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [sessionRefreshKey, setSessionRefreshKey] = useState(0)
  const sendingRef = useRef(false)

  function goToAuth(mode) {
    return (queryFromHero) => {
      setAuthMode(mode)
      if (queryFromHero && typeof queryFromHero === 'string') setPendingQuery(queryFromHero)
      setScreen('auth')
    }
  }

  function handleAuthed() {
    setScreen('chat')
    setGreeting(getGreeting())
    if (pendingQuery) {
      const q = pendingQuery
      setPendingQuery(null)
      handleSend(q)
    }
  }

  function handleLogout() {
    localStorage.removeItem('rune_token')
    localStorage.removeItem('rune_username')
    setMessages([])
    setSessionId(null)
    setScreen('landing')
  }

  async function handleSend(query) {
    if (sendingRef.current || !query) return
    sendingRef.current = true
    setLoading(true)
    const newMessage = { query, steps: [], answer: '' }
    setMessages(prev => [...prev, newMessage])
    try {
      const depth = localStorage.getItem('rune_depth') || 'deep'
      const token = localStorage.getItem('rune_token')
      const res = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query, session_id: sessionId, depth }),
      })
      if (res.status === 401) {
        handleLogout()
        return
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const event = JSON.parse(line.slice(6))
          setMessages(prev => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            if (event.type === 'step') last.steps.push(event.step)
            if (event.type === 'final') {
              last.answer = event.answer
              setSessionId(event.session_id)
              setSessionRefreshKey(k => k + 1)
            }
            if (event.type === 'error') last.answer = `Error: ${event.message}`
            return updated
          })
        }
      }
    } catch (err) {
      console.error('Query failed:', err)
    } finally {
      setLoading(false)
      sendingRef.current = false
    }
  }

  function handleNewResearch() {
    setMessages([])
    setSessionId(null)
  }

  async function handleLoadSession(id) {
    try {
      const token = localStorage.getItem('rune_token')
      const res = await fetch(`${API_URL}/sessions/${id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (res.status === 401) {
        handleLogout()
        return
      }
      const data = await res.json()
      const mapped = data.map(m => ({
        query: m.query,
        steps: m.trace || [],
        answer: m.final_answer,
      }))
      setMessages(mapped)
      setSessionId(id)
    } catch (err) {
      console.error('Failed to load session:', err)
    }
  }

  function handleSettingsSaved() {
    setGreeting(getGreeting())
    setSessionRefreshKey(k => k + 1)
  }

  if (screen === 'landing') {
    return <LandingPage onGetStarted={goToAuth('signup')} onLogin={goToAuth('login')} />
  }

  if (screen === 'auth') {
    return (
      <AuthPage
        mode={authMode}
        onAuthed={handleAuthed}
        onBack={() => setScreen('landing')}
      />
    )
  }

  const isEmpty = messages.length === 0

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <Sidebar
        open={sidebarOpen}
        onNewResearch={handleNewResearch}
        onLoadSession={handleLoadSession}
        activeSessionId={sessionId}
        onOpenSettings={() => setSettingsOpen(true)}
        onLogout={handleLogout}
        refreshKey={sessionRefreshKey}
      />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <div style={{ padding: '0.75rem 1rem' }}>
          <button
            onClick={() => setSidebarOpen(o => !o)}
            onMouseEnter={() => setHoverToggle(true)}
            onMouseLeave={() => setHoverToggle(false)}
            aria-label="Toggle sidebar"
            style={{
              background: hoverToggle ? 'rgba(0, 0, 0, 0.06)' : 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: 6,
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#4a4a4a',
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
              <rect x="3" y="4" width="18" height="16" rx="3" />
              <line x1="9.5" y1="4" x2="9.5" y2="20" />
            </svg>
          </button>
        </div>

        {isEmpty ? (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            paddingBottom: '6vh',
          }}>
            <div style={{ width: '100%', maxWidth: CONTENT_WIDTH, padding: '0 2rem', boxSizing: 'border-box' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: 14,
                marginBottom: '2rem',
              }}>
                <img src="/Rune.png" alt="Rune logo" width="32" height="32" style={{ objectFit: 'contain', borderRadius: 4 }} />
                <span className="serif" style={{ fontSize: 44 }}>{greeting}</span>
              </div>
              <InputBar onSend={handleSend} disabled={loading} />
            </div>
          </div>
        ) : (
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: 0 }}>
            <div style={{ width: '100%', maxWidth: CONTENT_WIDTH, padding: '1.5rem 2rem 0', boxSizing: 'border-box' }}>
              <ChatThread messages={messages} />
            </div>
            <div style={{ width: '100%', maxWidth: CONTENT_WIDTH, padding: '1rem 2rem 1.25rem', boxSizing: 'border-box', marginTop: 'auto' }}>
              <InputBar onSend={handleSend} disabled={loading} />
            </div>
          </div>
        )}
      </div>

      {settingsOpen && (
        <SettingsModal
          onClose={() => setSettingsOpen(false)}
          onSave={handleSettingsSaved}
        />
      )}
    </div>
  )
}