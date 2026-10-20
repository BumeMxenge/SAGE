// Course History as Mbali, beside the planner prototype's, in both themes: the page as it opens, and
// her newest year in full, as a photograph stops at the window's edge. routes.spec.ts already runs axe
// and the keyboard walk on this page once its h1 shows, and the page shows nothing until her record has
// arrived, so those checks see her tables. Nothing here is interactive, so there is no hover.
import { type Locator, type Page, test } from '@playwright/test'
import { type ParityCase, parity, type Theme } from '../../../e2e/parity.ts'
import { settled } from '../../../e2e/settled.ts'
import { mbali } from '../../../e2e/visitors.ts'

test.use({ storageState: mbali })

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
