// The sign-in landing, signed out: one gesture moves exactly one highlight, and each highlight's picture
// is one image to a screen reader. Then parity against the onboarding prototype's Landing state: the
// whole page with each highlight, and the controls it adds, at rest and on hover. Onboarding is light
// only, so it all runs in light alone.
import { expect, type Locator, type Page, test } from '@playwright/test'
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

const shown = (page: Page) => page.getByRole('tab', { selected: true })

test('one swipe, drag or trackpad gesture moves exactly one highlight, round and round', async ({ page }) => {
  await page.goto('/sign-in')
  await arrived(page, timetables)
  // A trackpad's sideways scroll arrives as a burst of wheel events, its momentum included. Twelve,
  // as a step on every event past the first would make eleven, which can't land on the next highlight.
  await page.getByRole('tabpanel').evaluate((panel) => {
    for (let event = 0; event < 12; event++) {
      panel.dispatchEvent(new WheelEvent('wheel', { deltaX: 40, bubbles: true, cancelable: true }))
    }
  })
  await expect(shown(page)).toHaveAccessibleName(answers)
  // A drag to the left moves on one, and on from the last highlight is the first. Each drag waits for
  // the strip to finish sliding, so it starts on the highlight at rest.
  for (const next of [credits, timetables]) {
    await settled(page)
    const panel = await page.getByRole('tabpanel').boundingBox()
    if (!panel) throw new Error('no highlight on screen')
    const middle = panel.y + panel.height / 2
    await page.mouse.move(panel.x + panel.width - 40, middle)
    await page.mouse.down()
    await page.mouse.move(panel.x + 40, middle, { steps: 8 })
    await page.mouse.up()
    await expect(shown(page)).toHaveAccessibleName(next)
  }
})

// White text on the prototype's teal is under 4.5:1, which WCAG 1.4.3 allows only for text that is
// part of a picture, so each picture must reach a screen reader as one named image and nothing more
test("each highlight's picture is one image to a screen reader", async ({ page }) => {
  await page.goto('/sign-in')
  await arrived(page, timetables)
  for (const [title, picture] of [
    [timetables, /^STA2020F's practical, Wednesday 14:00 to 16:00, clashes/],
    [answers, /^A student asks whether they can take STA2020F/],
    [credits, /^Semester 1's credit load/],
  ] as const) {
    await page.getByRole('tab', { name: title }).click()
    await expect(page.getByRole('tabpanel')).toMatchAriaSnapshot(`
      - heading "${title}" [level=2]
      - img ${String(picture)}
    `)
  }
})

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
