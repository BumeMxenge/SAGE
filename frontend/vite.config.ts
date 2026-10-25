// Vite and Vitest settings: React, the '@/' import alias from tsconfig, and port 3000 for both
// `npm run dev` and `npm run preview`
import react from '@vitejs/plugin-react'
import { searchForWorkspaceRoot } from 'vite'
import svgr from 'vite-plugin-svgr'
import { defineConfig } from 'vitest/config'

// Stop with an error if the port is taken, rather than quietly moving on, so each frontend stays
// on a port the backend's CORS list allows: 3000, or 3001 or 3002 for a worktree, which picks its
// own with `npm run dev -- --port 3001`
const port = { port: 3000, strictPort: true }

export default defineConfig({
  // dimensions: false and titleProp let CSS size each SVG and give each logo its own title id.
  // runtimeConfig: false, so a stray .svgrrc can never change the output.
  plugins: [svgr({ svgrOptions: { dimensions: false, titleProp: true, runtimeConfig: false } }), react()],
  // dedupe: the generated SVG components import react, which can't be found from ../assets/brand
  resolve: { tsconfigPaths: true, dedupe: ['react'] },
  // CSS Module classes are kebab-case in the stylesheet and camelCase in TypeScript: styles.iconButton
  css: { modules: { localsConvention: 'camelCaseOnly' } },
  // The logos live in ../assets/brand, with the README's banner, so the brand files share a folder.
  // The dev server only serves SVG imports from allowed folders, and the default is this one.
  server: { ...port, fs: { allow: [searchForWorkspaceRoot(import.meta.dirname), '../assets/brand'] } },
  preview: port,
  // The libraries every page loads with the app go in two files of their own, React with its router
  // and the API and sign-in clients, so no file passes Vite's 500 kB warning. Each group takes its
  // packages' own dependencies with it. React Aria stays split among the pages that use it.
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: 'react', test: /node_modules[\\/](react|react-dom|react-router)[\\/]/ },
            { name: 'clients', test: /node_modules[\\/](@supabase|@tanstack|openapi-fetch|openapi-react-query)[\\/]/ },
          ],
        },
      },
    },
  },
  // css: true, because Vitest otherwise turns every stylesheet, even ?raw, into an empty string. The
  // settings are made up, on .test hosts that never resolve, so no test reads frontend/.env or reaches
  // a real service.
  test: {
    environment: 'jsdom',
    css: true,
    include: ['src/**/*.test.{ts,tsx}', 'scripts/**/*.test.ts'],
    env: {
      VITE_API_URL: 'http://api.sage.test',
      VITE_SUPABASE_URL: 'http://supabase.sage.test',
      VITE_SUPABASE_PUBLISHABLE_KEY: 'made-up-publishable-key',
    },
  },
})
