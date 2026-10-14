// Vite settings: React, the '@/' import alias from tsconfig, and port 3000 for both `npm run dev` and
// `npm run preview`
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Stop with an error if the port is taken, rather than quietly moving on, so each frontend stays
// on a port the backend's CORS list allows: 3000, or 3001 or 3002 for a worktree, which picks its
// own with `npm run dev -- --port 3001`
const port = { port: 3000, strictPort: true }

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: { tsconfigPaths: true },
  // light-dark() works natively from these versions. Vite's older default would rewrite it into a
  // fallback trick that dev builds don't use, and dev and production would differ.
  build: { cssTarget: ['chrome123', 'edge123', 'firefox120', 'safari17.5'] },
  server: port,
  preview: port,
})
