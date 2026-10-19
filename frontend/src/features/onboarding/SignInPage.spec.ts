// Parity for the sign-in landing, signed out, against the onboarding prototype's Landing state: the
// whole page with each highlight, and the controls it adds, at rest and on hover. Onboarding has no
// dark design, so dark images show React alone.
import type { Page } from '@playwright/test'
import { type ParityCase, parity } from '../../../e2e/parity.ts'

const answers = 'Instant Answers, Grounded in the EBE Handbook'
const credits = 'Course Lists That Sit Inside Your Credit Limits'

// The prototype's Landing state, with its own state switcher taken off so it stays out of the image
async function landing(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Landing', exact: true }).click()
  await page.getByText('STATES', { exact: true }).locator('..').evaluate((switcher) => switcher.remove())
}

// Waits for a highlight to finish arriving, in either the prototype or React
async function settled(page: Page): Promise<void> {
  await page.waitForFunction(() => document.getAnimations().every((animation) => animation.playState !== 'running'))
}

// React's page loads after the address does, so its highlight appears first, then settles
async function arrived(page: Page, title = 'Timetables That Work in Practice, Not Just on Paper'): Promise<void> {
  await page.getByRole('heading', { name: title }).waitFor()
  await settled(page)
}

const whole = (page: Page) => page.locator('body')

// The landing with another highlight chosen: by its dot in the prototype, by its tab in React
function highlight(name: string, dot: number, tab: string): ParityCase {
  return {
    name,
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null
      await landing(page)
      await page.getByRole('button', { name: 'Highlight' }).nth(dot).click()
      await settled(page)
      return whole(page)
    },
    react: {
      path: '/sign-in',
      reach: async (page) => {
        await page.getByRole('tab', { name: tab }).click()
        await arrived(page, tab)
      },
      element: whole,
    },
  }
}

parity('onboarding', [
  {
    name: 'landing',
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null
      await landing(page)
      await settled(page)
      return whole(page)
    },
    react: { path: '/sign-in', reach: (page) => arrived(page), element: whole },
  },
  highlight('landing-answers', 1, answers),
  highlight('landing-credits', 2, credits),
  {
    name: 'sign-in-button',
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null
      await landing(page)
      return page.getByRole('button', { name: 'Continue with UCT email' })
    },
    react: { path: '/sign-in', element: (page) => page.getByRole('button', { name: 'Continue with UCT Email' }) },
    hover: true,
  },
  {
    name: 'highlight-dot',
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null
      await landing(page)
      return page.getByRole('button', { name: 'Highlight' }).nth(1)
    },
    react: { path: '/sign-in', element: (page) => page.getByRole('tab', { name: answers }) },
    hover: true,
  },
  {
    name: 'privacy-link',
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null
      await landing(page)
      return page.getByRole('link', { name: 'Privacy Policy' })
    },
    react: { path: '/sign-in', element: (page) => page.getByRole('link', { name: 'Privacy Policy' }) },
    hover: true,
  },
])
