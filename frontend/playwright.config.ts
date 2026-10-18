// The UI checks: axe, the keyboard walk and the parity images, against the local stack, in light and
// dark at 1280 by 820. make check-ui runs them, never CI, as they need local Supabase and the backend.
import { defineConfig } from '@playwright/test'

// This worktree's frontend: 3000, or 3001 or 3002 for a second worktree, as PORT says
const port = process.env.PORT ?? '3000'

export default defineConfig({
  // Specs sit in feature folders beside Vitest's tests, which end .test.ts, so neither runner loads
  // the other's files
  testDir: 'src',
  testMatch: '**/*.spec.ts',
  // Traces, screenshots and video stay off, as by default, so no session token lands in a file
  reporter: 'list',
  use: { baseURL: `http://localhost:${port}`, viewport: { width: 1280, height: 820 } },
  projects: [
    { name: 'sign-in', testDir: 'e2e', testMatch: 'sign-in.setup.ts' },
    { name: 'light', use: { colorScheme: 'light' }, dependencies: ['sign-in'] },
    { name: 'dark', use: { colorScheme: 'dark' }, dependencies: ['sign-in'] },
  ],
  // This worktree's frontend, started if it isn't already running on the port
  webServer: { command: `npm run dev -- --port ${port}`, url: `http://localhost:${port}`, reuseExistingServer: true },
})
