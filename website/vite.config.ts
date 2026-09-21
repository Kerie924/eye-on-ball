import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'https://api.lanceonpara.com.br',
        changeOrigin: true,
        secure: true,
      },
      '/health': {
        target: 'https://api.lanceonpara.com.br',
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
