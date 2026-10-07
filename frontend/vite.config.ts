// Vite settings: React, and port 3000 for both `npm run dev` and `npm run preview`
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Stop with an error if port 3000 is taken, rather than quietly moving to 3001:
// the backend's CORS list and Supabase's redirect list only allow 3000
const port = { port: 3000, strictPort: true }

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: port,
  preview: port,
})
