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

// https://vite.dev/config/
export default defineConfig({
  // dimensions: false and titleProp let CSS size each SVG and give each logo its own title id.
  // runtimeConfig: false, so a stray .svgrrc can never change the output.
  plugins: [svgr({ svgrOptions: { dimensions: false, titleProp: true, runtimeConfig: false } }), react()],
  // dedupe: the generated SVG components import react, which can't be found from ../assets/brand
  resolve: { tsconfigPaths: true, dedupe: ['react'] },
  // light-dark() works natively from these versions. Vite's older default would rewrite it into a
  // fallback trick that dev builds don't use, and dev and production would differ.
  css: { modules: { localsConvention: 'camelCaseOnly' } },
  build: { cssTarget: ['chrome123', 'edge123', 'firefox120', 'safari17.5'] },
  // The logos live in ../assets/brand, so the README and the app share one copy. The dev server only
  // serves SVG imports from allowed folders, and the default is this one.
  server: { ...port, fs: { allow: [searchForWorkspaceRoot(import.meta.dirname), '../assets/brand'] } },
  preview: port,
  // css: true, because Vitest otherwise turns every stylesheet, even ?raw, into an empty string
  test: { environment: 'jsdom', css: true, include: ['src/**/*.test.{ts,tsx}', 'scripts/**/*.test.ts'] },
})
