import ReactMarkdown from 'react-markdown'
import { useState, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

function stripCitations(text) {
  // Matches [1], [1, 3], [2] etc. and removes them along with the space before.
  return text.replace(/\s?\[\d+(?:,\s*\d+)*\]/g, '')
}

export default function ChatThread({ messages }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1.5rem',
      width: '100%',
      maxWidth: 720,
      margin: '0 auto',
      boxSizing: 'border-box',
    }}>
      {messages.map((m, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem', width: '100%' }}>
          <div style={{
            alignSelf: 'flex-end', maxWidth: '65%', background: '#ECE9E1',
            color: '#1C1917', padding: '14px 18px', borderRadius: 18, fontSize: 15,
          }}>
            {m.query}
          </div>
          {m.steps.length > 0 && (
            <div style={{ width: '92%', boxSizing: 'border-box' }}>
              <TraceCard steps={m.steps} isStreaming={!m.answer} />
              {m.answer && !m.answer.startsWith('Error:') && (
                <AnswerBlock text={m.answer} />
              )}
              {m.answer && m.answer.startsWith('Error:') && (
                <ErrorBox message={m.answer.replace('Error: ', '')} />
              )}
            </div>
          )}
          {m.steps.length === 0 && !m.answer && (
            <div style={{ width: '92%' }}>
              <ThinkingIndicator />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function AnswerBlock({ text }) {
  const [copied, setCopied] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [ttsLoading, setTtsLoading] = useState(false)
  const audioRef = useRef(null)
  const cleanText = stripCitations(text)

  function handleCopy() {
    navigator.clipboard.writeText(cleanText)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  async function handleListen() {
    if (speaking && audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
      setSpeaking(false)
      return
    }

    setTtsLoading(true)
    try {
      const token = localStorage.getItem('rune_token')
      const res = await fetch(`${API_URL}/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ text: cleanText, language_code: 'en-IN' }),
      })
      if (!res.ok) throw new Error('TTS request failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current = audio
      audio.onended = () => setSpeaking(false)
      audio.play()
      setSpeaking(true)
    } catch (err) {
      console.error('TTS failed:', err)
    } finally {
      setTtsLoading(false)
    }
  }

  return (
    <div style={{ marginTop: 10 }}>
      <div className="markdown-answer" style={{ fontSize: 15, lineHeight: 1.7 }}>
        <ReactMarkdown>{cleanText}</ReactMarkdown>
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <button
          onClick={handleCopy}
          style={{
            background: 'transparent',
            border: '0.5px solid #d8d2c4',
            borderRadius: 6,
            padding: '5px 10px',
            fontSize: 12,
            color: '#8a8578',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 5,
          }}
        >
          {copied ? (
            <>✓ Copied</>
          ) : (
            <>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              Copy
            </>
          )}
        </button>

        <button
          onClick={handleListen}
          disabled={ttsLoading}
          style={{
            background: speaking ? '#ECE9E1' : 'transparent',
            border: '0.5px solid #d8d2c4',
            borderRadius: 6,
            padding: '5px 10px',
            fontSize: 12,
            color: '#8a8578',
            cursor: ttsLoading ? 'default' : 'pointer',
            opacity: ttsLoading ? 0.6 : 1,
            display: 'flex',
            alignItems: 'center',
            gap: 5,
          }}
        >
          {ttsLoading ? (
            <>Loading…</>
          ) : speaking ? (
            <>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="5" width="4" height="14" />
                <rect x="14" y="5" width="4" height="14" />
              </svg>
              Stop
            </>
          ) : (
            <>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
              </svg>
              Listen
            </>
          )}
        </button>
      </div>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      fontSize: 13, color: '#8a9a72', padding: '4px 2px',
    }}>
      <span className="mono">thinking</span>
      <span style={{ display: 'flex', gap: 3 }}>
        <Dot delay="0s" />
        <Dot delay="0.15s" />
        <Dot delay="0.3s" />
      </span>
    </div>
  )
}

function Dot({ delay }) {
  return (
    <span style={{
      width: 4, height: 4, borderRadius: '50%', background: '#8a9a72',
      display: 'inline-block', animation: 'rune-pulse 1s infinite ease-in-out',
      animationDelay: delay,
    }} />
  )
}

function ErrorBox({ message }) {
  return (
    <div style={{
      background: '#FBEAE9', border: '0.5px solid #E8B4B0', borderRadius: 12,
      padding: '12px 16px', fontSize: 13.5, color: '#9C3B34', marginTop: 8,
      display: 'flex', alignItems: 'flex-start', gap: 8,
    }}>
      <span style={{ fontSize: 15 }}>⚠</span>
      <span>{message}</span>
    </div>
  )
}

function TraceCard({ steps, isStreaming }) {
  return (
    <div style={{
      border: '0.5px solid #e5e2da', background: '#fff', borderRadius: 12,
      padding: '0.85rem 1.1rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      width: '100%', boxSizing: 'border-box',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
        <span className="mono" style={{ fontSize: 10, letterSpacing: '0.05em', color: '#8a9a72' }}>
          {isStreaming ? 'thinking…' : 'thinking'}
        </span>
        <span style={{ fontSize: 10, color: '#a39c8d' }}>{steps.length} steps</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
        {steps.map((s, i) => (
          <div key={i} style={{ fontSize: 12.5, color: '#5c574c' }}>
            <b style={{ color: '#1C1917' }}>{s.node}</b> — {s.summary}
          </div>
        ))}
      </div>
    </div>
  )
}