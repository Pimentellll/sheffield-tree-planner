import { readFileSync } from 'node:fs'
import type { Plugin } from 'vite'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Local backend started by scripts/serve_reference.py (or `python -m tree_planner.api`).
const backend = process.env.CANOPY_API ?? 'http://127.0.0.1:8765'
// Session file written by scripts/serve_reference.py: scenario identity + exact synthetic asset bytes.
const sessionFile = process.env.CANOPY_SESSION

/** Serve the launcher's session at /canopy-dev-session.json (dev server only). */
function devSession(): Plugin {
  return {
    name: 'canopy-dev-session',
    configureServer(server) {
      server.middlewares.use('/canopy-dev-session.json', (_req, res) => {
        if (!sessionFile) { res.statusCode = 404; res.end('{}'); return }
        try {
          const body = readFileSync(sessionFile)
          res.setHeader('Content-Type', 'application/json')
          res.setHeader('Cache-Control', 'no-store')
          res.end(body)
        } catch {
          res.statusCode = 404
          res.end('{}')
        }
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), devSession()],
  server: {
    proxy: {
      // The backend only accepts same-origin (or explicitly allowed) loopback origins.
      // The dev proxy is the browser's single origin, so present the backend's own origin.
      '/api': {
        target: backend,
        changeOrigin: true,
        configure: proxy => {
          proxy.on('proxyReq', proxyReq => {
            if (proxyReq.getHeader('origin')) proxyReq.setHeader('origin', new URL(backend).origin)
          })
        },
      },
    },
  },
  test: {
    // .tsx for hook tests; those opt into jsdom per file (`// @vitest-environment jsdom`), the rest stay in node.
    include: ['src/**/*.test.{ts,tsx}'],
    environment: 'node',
  },
})
