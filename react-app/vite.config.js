import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:5000',
      '/upload': 'http://localhost:5000',
      '/auth': 'http://localhost:5000',
      '/admin': 'http://localhost:5000',
    }
  }
})
