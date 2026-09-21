import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/admin/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://13.210.97.155:8000',
      '/health': 'http://13.210.97.155:8000',
    },
  },
})
