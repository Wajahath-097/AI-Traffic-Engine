import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const printLoginUrlPlugin = () => ({
  name: 'print-login-url',
  configureServer(server) {
    server.httpServer?.once('listening', () => {
      setTimeout(() => {
        console.log('\n  👉 Login Page URL: \x1b[36mhttp://localhost:5173/login\x1b[0m\n')
      }, 100)
    })
  }
})

export default defineConfig({
  plugins: [react(), printLoginUrlPlugin()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    watch: {
      usePolling: true,
      interval: 1000,
      ignored: ['**/node_modules/**', '**/.git/**']
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
