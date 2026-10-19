// Parity for the sign-in landing, signed out, against the onboarding prototype's Landing state: the
// whole page with each highlight, and the controls it adds, at rest and on hover. Onboarding is light
// only, so parity runs in light alone.
import { type Locator, type Page, test } from '@playwright/test'
import { type ParityCase, parity } from '../../../e2e/parity.ts'
import { settled, showState } from './prototype.ts'

const timetables = 'Timetables That Work in Practice, Not Just on Paper'
const answers = 'Instant Answers, Grounded in the EBE Handbook'
const credits = 'Course Lists That Sit Inside Your Credit Limits'

// React's page loads after the address does, so its highlight appears first, then settles
async function arrived(page: Page, title: string): Promise<void> {
  await page.getByRole('heading', { name: title }).waitFor()
  await settled(page)
}

const whole = (page: Page) => page.locator('body')

// The landing with one highlight chosen: by its dot in the prototype, and by its tab in React
function highlight(name: string, dot: number, tab: string): ParityCase {
  return {
    name,
    prototype: 'onboarding',
    reach: async (page) => {
      await showState(page, 'Landing')
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

// One control of the landing, at rest and on hover
function control(name: string, designed: (page: Page) => Locator, built: (page: Page) => Locator): ParityCase {
  return {
    name,
    prototype: 'onboarding',
    reach: async (page) => {
      await showState(page, 'Landing')
      return designed(page)
    },
    react: { path: '/sign-in', element: built },
    hover: true,
  }
}

test.skip(({ colorScheme }) => colorScheme === 'dark', 'Onboarding is light only')

parity('onboarding', [
  {
    name: 'landing',
    prototype: 'onboarding',
    reach: async (page) => {
      await showState(page, 'Landing')
      await settled(page)
      return whole(page)
    },
    react: { path: '/sign-in', reach: (page) => arrived(page, timetables), element: whole },
  },
  highlight('landing-answers', 1, answers),
  highlight('landing-credits', 2, credits),
  control(
    'sign-in-button',
    (page) => page.getByRole('button', { name: 'Continue with UCT email' }),
    (page) => page.getByRole('button', { name: 'Continue with UCT Email' }),
  ),
  control(
    'highlight-dot',
    (page) => page.getByRole('button', { name: 'Highlight' }).nth(1),
    (page) => page.getByRole('tab', { name: answers }),
  ),
  control(
    'privacy-link',
    (page) => page.getByRole('link', { name: 'Privacy Policy' }),
    (page) => page.getByRole('link', { name: 'Privacy Policy' }),
  ),
])
