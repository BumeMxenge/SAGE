// Course History as Mbali: its title and cumulative average stay in view as the page scrolls, its tables
// fill the page beside the sidebar, open or folded, and parity beside the planner prototype in both
// themes, the page as it opens and her newest year in full, as a photograph stops at the window's edge.
// routes.spec.ts already runs axe and the keyboard walk on this page once its h1 shows, and the page
// shows nothing until her record has arrived, so those checks see her tables. Nothing here is
// interactive, so there is no hover.
import { expect, type Locator, type Page, test } from '@playwright/test'
import { type ParityCase, parity, type Theme } from '../../../e2e/parity.ts'
import { settled } from '../../../e2e/settled.ts'
import { mbali } from '../../../e2e/visitors.ts'

test.use({ storageState: mbali })

async function scrollToFoot(page: Page): Promise<void> {
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight))
}

// From 400 px tall the header stays at the top of the window, as the prototype's does. One pixel
// shorter, it scrolls away with the tables, as it would cover too much of the screen.
test('the title and cumulative average stay in view to the foot of the page, from 400 px tall', async ({ page }) => {
  const title = page.getByRole('heading', { level: 1, name: 'Course History' })
  const average = page.getByText('Cumulative Average:')
  await page.setViewportSize({ width: 1280, height: 400 })
  await page.goto('/history')
  await title.waitFor()
  await scrollToFoot(page)
  await expect(title).toBeInViewport()
  await expect(average).toBeInViewport()
  await page.setViewportSize({ width: 1280, height: 399 })
  await scrollToFoot(page)
  await expect(title).not.toBeInViewport()
  await expect(average).not.toBeInViewport()
})

// How far the newest year's table stands in from the page's margins, on each side
async function gaps(page: Page): Promise<{ left: number; right: number }> {
  const margins = await page.getByRole('main').evaluate((main) => {
    const { left, right } = main.getBoundingClientRect()
    const style = getComputedStyle(main)
    return { left: left + parseFloat(style.paddingLeft), right: right - parseFloat(style.paddingRight) }
  })
  const table = await page
    .getByRole('table')
    .first()
    .evaluate((element) => {
      const { left, right } = element.getBoundingClientRect()
      return { left, right }
    })
  return { left: Math.abs(Math.round(table.left - margins.left)), right: Math.abs(Math.round(margins.right - table.right)) }
}

test('the tables run from one margin of the page to the other, beside the sidebar open or folded', async ({ page }) => {
  await page.goto('/history')
  await page.getByRole('heading', { level: 1 }).waitFor()
  expect(await gaps(page)).toEqual({ left: 0, right: 0 })
  await page.getByRole('button', { name: 'Collapse Sidebar' }).click()
  await settled(page)
  expect(await gaps(page)).toEqual({ left: 0, right: 0 })
})

// The prototype opens at the empty plan and reads its theme from its address. Its open sidebar is the
// aside screen readers can see, as AppLayout.spec.ts finds it.
async function prototypeHistory(page: Page, theme: Theme): Promise<void> {
  if (theme === 'dark') await page.goto(`${page.url()}?theme=dark`)
  await page.locator('aside[aria-hidden="false"]').getByRole('button', { name: 'Course history' }).click()
  await settled(page)
}

async function opened(page: Page): Promise<void> {
  await page.getByRole('heading', { level: 1 }).waitFor()
  await settled(page)
}

function photographed(name: string, designed: (page: Page) => Locator, built: (page: Page) => Locator): ParityCase {
  return {
    name,
    prototype: 'registration-planner',
    reach: async (page, theme) => {
      await prototypeHistory(page, theme)
      return designed(page)
    },
    react: { path: '/history', reach: opened, element: built },
  }
}

parity('history', [
  // Beside the sidebar, down to the window's edge
  photographed(
    'page',
    (page) => page.getByRole('heading', { name: 'Course history' }).locator('xpath=../../..'),
    (page) => page.getByRole('main'),
  ),
  // Her newest year: its title line and its table, which share the second div round the prototype's
  // title text
  photographed(
    'year',
    (page) => page.getByText('2025 · Third year').locator('xpath=ancestor::div[2]'),
    (page) => page.getByRole('table', { name: /^2025 / }),
  ),
])
