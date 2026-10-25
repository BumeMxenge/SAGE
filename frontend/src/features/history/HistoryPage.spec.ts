// Course History as Mbali: its title and cumulative average stay in view as the page scrolls, the page
// stands in from its margins beside the sidebar, open or folded, and parity beside the planner prototype
// in both themes, the page as it opens and her newest year in full, as a photograph stops at the
// window's edge. While her record is held on its way, loading case 05 shows, passes axe and is
// photographed beside the page it turns into; a refused read leaves no skeleton; and the page from the
// cache shows none and fades nothing in.
// routes.spec.ts already runs axe and the keyboard walk on this page once its record has arrived.
// Nothing here is interactive, so there is no hover.
import { expect, type Locator, type Page, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../../e2e/axe.ts'
import {
  forgetSeen,
  hold,
  loading,
  photographArrival,
  read,
  refusal,
  seenLoading,
  skeletons,
  watchLoading,
} from '../../../e2e/loading.ts'
import { type ParityCase, parity, type Theme } from '../../../e2e/parity.ts'
import { settled } from '../../../e2e/settled.ts'
import { mbali } from '../../../e2e/visitors.ts'

test.use({ storageState: mbali })

const title = (page: Page) => page.getByRole('heading', { level: 1, name: 'Course History' })
// Her newest year's table, once her record has arrived. The skeleton's table is hidden from screen
// readers, so it never matches.
const newestYear = (page: Page) => page.getByRole('table', { name: /^2025 / })

test("while her record is on its way, the title and the average's label show over a year's skeleton, which her record replaces", async ({
  page,
}, testInfo) => {
  await watchLoading(page)
  const record = await hold(page, read('/v1/history'))
  await page.goto('/history')
  await expect(title(page)).toBeVisible()
  await expect(page.getByText('Cumulative Average:')).toBeVisible()
  await expect(loading(page, 'Loading your course history…')).toBeAttached()
  await expect(skeletons(page.getByRole('main')).first()).toBeVisible()
  // The year's skeleton, under its real column headers
  await expect(page.getByRole('main').getByText('Result', { exact: true })).toBeVisible()
  await expectNoAxeViolations(page)
  await photographArrival(page, testInfo, 'history', () => record.release())
  await expect(newestYear(page)).toBeVisible()
  await expect(page.getByText(/^Cumulative Average: \d+\.\d%$/)).toBeVisible()
  // What took the skeleton's place faded in
  expect((await seenLoading(page)).fades).toBeGreaterThan(0)
})

test('a refused read leaves no skeleton', async ({ page }) => {
  const record = await hold(page, read('/v1/history'))
  await page.goto('/history')
  await expect(skeletons(page.getByRole('main')).first()).toBeVisible()
  // A refusal isn't tried again, so the read has failed at once
  await record.refuse(refusal('invalid_request', 422))
  await expect(skeletons(page.getByRole('main'))).toHaveCount(0)
  await expect(loading(page)).toHaveCount(0)
  await expect(title(page)).toBeVisible()
})

test('back from another page, her record shows from the cache at once, with no skeleton and no fade', async ({ page }) => {
  await watchLoading(page)
  await page.goto('/history')
  await newestYear(page).waitFor()
  await page.getByRole('link', { name: 'Plan', exact: true }).click()
  await page.getByRole('button', { name: 'Compare', exact: true }).waitFor()
  await forgetSeen(page)
  await page.getByRole('link', { name: 'Course History', exact: true }).click()
  await newestYear(page).waitFor()
  await settled(page)
  expect(await seenLoading(page)).toEqual({ skeletons: 0, fades: 0 })
})

async function scrollToFoot(page: Page): Promise<void> {
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight))
}

// From 400 px tall the header stays at the top of the window, as the prototype's does. One pixel
// shorter, it scrolls away with the tables, as it would cover too much of the screen.
test('the title and cumulative average stay in view to the foot of the page, from 400 px tall', async ({ page }) => {
  const average = page.getByText('Cumulative Average:')
  await page.setViewportSize({ width: 1280, height: 400 })
  await page.goto('/history')
  await newestYear(page).waitFor()
  await scrollToFoot(page)
  await expect(title(page)).toBeInViewport()
  await expect(average).toBeInViewport()
  await page.setViewportSize({ width: 1280, height: 399 })
  await scrollToFoot(page)
  await expect(title(page)).not.toBeInViewport()
  await expect(average).not.toBeInViewport()
})

// How far the title and the newest year's table stand in from the page area's left margin, and the
// cumulative average and that table from its right. Each edge is rounded on its own, so an exact fit
// reads 0, never the -0 that toEqual tells apart from it.
async function insets(page: Page): Promise<{ title: number; tableLeft: number; tableRight: number; average: number }> {
  const margins = await page.getByRole('main').evaluate((main) => {
    const { left, right } = main.getBoundingClientRect()
    const style = getComputedStyle(main)
    return { left: left + parseFloat(style.paddingLeft), right: right - parseFloat(style.paddingRight) }
  })
  const edges = (locator: Locator) =>
    locator.evaluate((element) => {
      const { left, right } = element.getBoundingClientRect()
      return { left, right }
    })
  const title = await edges(page.getByRole('heading', { level: 1 }))
  const table = await edges(page.getByRole('table').first())
  const average = await edges(page.getByText('Cumulative Average:'))
  return {
    title: Math.round(title.left) - Math.round(margins.left),
    tableLeft: Math.round(table.left) - Math.round(margins.left),
    tableRight: Math.round(margins.right) - Math.round(table.right),
    average: Math.round(margins.right) - Math.round(average.right),
  }
}

// From 768 px wide the page keeps 24 px more at each side, its title and cumulative average in line
// with its tables, as the sidebar opens and folds. A narrower window, as at 200% zoom, gives the
// tables that room.
test('the title and tables stand 24 px inside the margins from 768 px wide, beside the sidebar open or folded', async ({ page }) => {
  const inset = { title: 24, tableLeft: 24, tableRight: 24, average: 24 }
  await page.goto('/history')
  await newestYear(page).waitFor()
  expect(await insets(page)).toEqual(inset)
  await page.getByRole('button', { name: 'Collapse Sidebar' }).click()
  await settled(page)
  expect(await insets(page)).toEqual(inset)
  await page.setViewportSize({ width: 768, height: 820 })
  expect(await insets(page)).toEqual(inset)
  await page.setViewportSize({ width: 767, height: 820 })
  expect(await insets(page)).toEqual({ title: 0, tableLeft: 0, tableRight: 0, average: 0 })
})

// The prototype opens at the empty plan and reads its theme from its address. Its open sidebar is the
// aside screen readers can see, as AppLayout.spec.ts finds it.
async function prototypeHistory(page: Page, theme: Theme): Promise<void> {
  if (theme === 'dark') await page.goto(`${page.url()}?theme=dark`)
  await page.locator('aside[aria-hidden="false"]').getByRole('button', { name: 'Course history' }).click()
  await settled(page)
}

async function opened(page: Page): Promise<void> {
  await newestYear(page).waitFor()
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
