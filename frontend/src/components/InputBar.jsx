import { useState, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

export default function InputBar({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const fileInputRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  function submit() {
    if (!value.trim() || disabled) return
    onSend(value.trim())
    setValue('')
  }

  function handleFileSelect(e) {
    const file = e.target.files?.[0]
    if (file) {
      console.log('File selected:', file.name)
      // wire this up to your actual upload/attach logic later
    }
    e.target.value = ''
  }

  async function toggleRecording() {
    if (recording) {
      mediaRecorderRef.current?.stop()
      setRecording(false)
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop())
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
        await transcribe(audioBlob)
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setRecording(true)
    } catch (err) {
      console.error('Mic access failed:', err)
    }
  }

  async function transcribe(audioBlob) {
    setTranscribing(true)
    try {
      const token = localStorage.getItem('rune_token')
      const formData = new FormData()
      formData.append('file', audioBlob, 'recording.webm')
      formData.append('language_code', 'unknown')

      const res = await fetch(`${API_URL}/stt`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      })
      if (!res.ok) throw new Error('STT request failed')
      const data = await res.json()
      setValue(prev => (prev ? `${prev} ${data.transcript}` : data.transcript))
    } catch (err) {
      console.error('STT failed:', err)
    } finally {
      setTranscribing(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
      background: '#fff',
      border: '0.5px solid #e5e2da',
      borderRadius: 26,
      padding: '20px 24px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.04)',
      maxWidth: 720,
      width: '100%',
      margin: '0 auto',
    }}>
      <input
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && submit()}
        placeholder={transcribing ? 'Transcribing…' : 'Give me a topic, question, or claim to research...'}
        disabled={disabled || transcribing}
        style={{ border: 'none', background: 'transparent', fontSize: 16, outline: 'none' }}
      />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <button
          onClick={() => fileInputRef.current?.click()}
          aria-label="Attach file"
          style={{
            background: 'transparent',
            border: '1px solid #d8d2c4',
            borderRadius: 8,
            cursor: 'pointer',
            width: 30,
            height: 30,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#5c574c',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={toggleRecording}
            disabled={transcribing}
            aria-label={recording ? 'Stop recording' : 'Start recording'}
            style={{
              background: recording ? '#E8B4B0' : 'transparent',
              border: '1px solid #d8d2c4',
              borderRadius: 8,
              cursor: transcribing ? 'default' : 'pointer',
              width: 30,
              height: 30,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: recording ? '#9C3B34' : '#5c574c',
              opacity: transcribing ? 0.6 : 1,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
              <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
              <line x1="12" y1="18" x2="12" y2="22" />
            </svg>
          </button>

          <button
            onClick={submit}
            disabled={disabled}
            aria-label="Send"
            style={{
              background: '#B8C4A8',
              border: 'none',
              borderRadius: 10,
              width: 34,
              height: 34,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: disabled ? 'default' : 'pointer',
              opacity: disabled ? 0.6 : 1,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}