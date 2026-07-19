import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/query': 'http://localhost:8000',
      '/sessions': 'http://localhost:8000',
      '/tts': 'http://localhost:8000',
      '/stt': 'http://localhost:8000',
    },
  },
})