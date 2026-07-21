import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

export default function Sidebar({ open, onNewResearch, onLoadSession, activeSessionId, onOpenSettings, onLogout, refreshKey }) {
  const [sessions, setSessions] = useState([])
  const [username, setUsername] = useState(() => localStorage.getItem('rune_username') || 'Account')

  useEffect(() => {
    const token = localStorage.getItem('rune_token')
    fetch(`${API_URL}/sessions`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(r => r.json())
      .then(setSessions)
      .catch(() => {})
  }, [refreshKey])

  // Re-read the username whenever refreshKey changes (App.jsx bumps this
  // after settings are saved), so a name change shows up immediately
  // without needing a full page reload.
  useEffect(() => {
    setUsername(localStorage.getItem('rune_username') || 'Account')
  }, [refreshKey])

  const initial = username.trim().charAt(0).toUpperCase() || 'A'

  return (
    <div style={{
      width: open ? 230 : 0,
      overflow: 'hidden',
      background: '#FAFAF8',
      borderRight: open ? '0.5px solid #e5e2da' : 'none',
      padding: open ? '1.1rem 1rem' : '1.1rem 0',
      display: 'flex',
      flexDirection: 'column',
      gap: '1.3rem',
      flexShrink: 0,
      transition: 'width 0.2s ease, padding 0.2s ease',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, whiteSpace: 'nowrap' }}>
        <img src="/Rune.png" alt="Rune logo" width="24" height="24" style={{ objectFit: 'contain', borderRadius: 4 }} />
        <span className="serif" style={{ fontSize: 19, color: '#1C1917' }}>Rune</span>
      </div>
      <button
        onClick={onNewResearch}
        style={{
          display: 'flex', alignItems: 'center', gap: 6, background: '#fff',
          border: '0.5px solid #d8d2c4', color: '#5c574c', borderRadius: 8,
          padding: '9px 12px', fontSize: 13, textAlign: 'left', cursor: 'pointer',
          whiteSpace: 'nowrap',
        }}
      >
        + New research
      </button>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <p className="mono" style={{ fontSize: 11, letterSpacing: '0.05em', color: '#a39c8d', marginBottom: 8 }}>
          recent
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {sessions.map(s => (
            <div
              key={s.id}
              onClick={() => onLoadSession(s.id)}
              style={{
                fontSize: 13,
                color: s.id === activeSessionId ? '#1C1917' : '#5c574c',
                background: s.id === activeSessionId ? '#ECE9E1' : 'transparent',
                fontWeight: s.id === activeSessionId ? 500 : 400,
                padding: 8, borderRadius: 6,
                cursor: 'pointer', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              }}
            >
              {s.title}
            </div>
          ))}
          {sessions.length === 0 && (
            <p style={{ fontSize: 12, color: '#c4bfb2' }}>No sessions yet</p>
          )}
        </div>
      </div>
      <div
        onClick={onOpenSettings}
        style={{
          borderTop: '0.5px solid #e5e2da', paddingTop: 12, display: 'flex', alignItems: 'center', gap: 8,
          cursor: 'pointer', borderRadius: 6, padding: '10px 6px',
        }}
      >
        <div style={{
          width: 24, height: 24, borderRadius: '50%', background: '#B8C4A8',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 500,
        }}>{initial}</div>
        <span style={{ fontSize: 12.5, color: '#5c574c' }}>{username}</span>
      </div>
      <button
        onClick={onLogout}
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          fontSize: 12, color: '#a39c8d', textAlign: 'left', padding: '0 6px',
        }}
      >
        Log out
      </button>
    </div>
  )
}