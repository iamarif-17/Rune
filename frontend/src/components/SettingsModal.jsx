import { useState } from 'react'

export default function SettingsModal({ onClose, onSave }) {
  const [name, setName] = useState(localStorage.getItem('rune_username') || '')
  const [depth, setDepth] = useState(localStorage.getItem('rune_depth') || 'deep')

  function handleSave() {
    if (name.trim()) {
      localStorage.setItem('rune_username', name.trim())
    } else {
      localStorage.removeItem('rune_username')
    }
    localStorage.setItem('rune_depth', depth)
    onSave()
    onClose()
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#fff', borderRadius: 16, padding: '1.75rem',
          width: 340, boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
        }}
      >
        <h2 className="serif" style={{ fontSize: 20, marginBottom: 4 }}>Settings</h2>
        <p style={{ fontSize: 13, color: '#8a8578', marginBottom: 20 }}>
          Your name is used for the greeting on the home screen.
        </p>
        <label style={{ fontSize: 12.5, color: '#5c574c', display: 'block', marginBottom: 6 }}>
          Your name
        </label>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSave()}
          placeholder="e.g. Arif"
          style={{
            width: '100%', border: '0.5px solid #d8d2c4', borderRadius: 8,
            padding: '10px 12px', fontSize: 14, outline: 'none', marginBottom: 20,
          }}
        />

        <label style={{ fontSize: 12.5, color: '#5c574c', display: 'block', marginBottom: 6 }}>
          Research depth
        </label>
        <p style={{ fontSize: 12, color: '#a39c8d', marginBottom: 10 }}>
          Shallow uses fewer API calls per query. Useful if you're hitting rate limits.
        </p>
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          <button
            onClick={() => setDepth('shallow')}
            style={{
              flex: 1, padding: '10px 0', borderRadius: 8, fontSize: 13, cursor: 'pointer',
              border: depth === 'shallow' ? '1.5px solid #B8C4A8' : '0.5px solid #d8d2c4',
              background: depth === 'shallow' ? '#F0F3EC' : '#fff',
              color: depth === 'shallow' ? '#5c6b4a' : '#8a8578',
              fontWeight: depth === 'shallow' ? 600 : 400,
            }}
          >
            Shallow
          </button>
          <button
            onClick={() => setDepth('deep')}
            style={{
              flex: 1, padding: '10px 0', borderRadius: 8, fontSize: 13, cursor: 'pointer',
              border: depth === 'deep' ? '1.5px solid #B8C4A8' : '0.5px solid #d8d2c4',
              background: depth === 'deep' ? '#F0F3EC' : '#fff',
              color: depth === 'deep' ? '#5c6b4a' : '#8a8578',
              fontWeight: depth === 'deep' ? 600 : 400,
            }}
          >
            Deep
          </button>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button
            onClick={onClose}
            style={{
              background: 'transparent', border: 'none', color: '#8a8578',
              fontSize: 13, padding: '8px 14px', cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            style={{
              background: '#B8C4A8', border: 'none', borderRadius: 8, color: '#fff',
              fontSize: 13, padding: '8px 16px', cursor: 'pointer', fontWeight: 500,
            }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  )
}