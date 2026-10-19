// Parity for onboarding's steps, as a student who hasn't finished setup: Mbali's session with a made-up
// answer from GET /v1/me, so no check resets a real account. Onboarding has no dark design, so dark
// images show React alone.
import { test } from '@playwright/test'
import { parity } from '../../../e2e/parity.ts'
import { mbali, visitAs } from '../../../e2e/visitors.ts'
import { settled, showState } from './prototype.ts'

test.use({ storageState: mbali })

test.beforeEach(async ({ page }) => {
  await visitAs(page, 'unfinished')
})

parity('onboarding', [
  {
    name: 'account-created',
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null
      await showState(page, 'Account created')
      await settled(page)
      return page.locator('body')
    },
    react: {
      path: '/onboarding',
      // The confetti falls once, then the page is still
      reach: async (page) => {
        await page.getByRole('heading', { level: 1 }).waitFor()
        await settled(page)
      },
      element: (page) => page.locator('body'),
    },
  },
  {
    name: 'next-button',
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null
      await showState(page, 'Account created')
      return page.getByRole('button', { name: 'Next, your course history' })
    },
    react: { path: '/onboarding', element: (page) => page.getByRole('button', { name: 'Next, Your Course History' }) },
    hover: true,
  },
])
