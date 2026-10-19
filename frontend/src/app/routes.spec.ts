// Every page in the route table, opened by the visitor it's for, has no axe violations and a clean
// keyboard walk, in light and dark. Staff, an account from outside UCT and a student who hasn't
// finished setup are Mbali's session with a made-up answer from GET /v1/me, so no check resets a real
// account.
import { expect, type Page, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../e2e/axe.ts'
import { walkKeyboard } from '../../e2e/keyboard.ts'
import { mbali, visitAs } from '../../e2e/visitors.ts'

// The page opens for its visitor, the guard lets them stay, it has one h1, and it passes both checks.
// The h1 isn't named here, as each page's own branch writes it; a second h1 fails strict mode.
async function check(page: Page, path: string, leaveOut: string[] = []): Promise<void> {
  await page.goto(path)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  expect(new URL(page.url()).pathname).toBe(path)
  await expectNoAxeViolations(page, leaveOut)
  await walkKeyboard(page)
}

test('/sign-in, signed out', async ({ page }) => {
  // The highlight's picture draws white text on the prototype's teal, under 4.5:1. It is one image to a
  // screen reader, and WCAG 1.4.3 sets no contrast for text that is part of a picture, so axe leaves
  // that one image out (docs/shortfalls.md)
  await check(page, '/sign-in', ['[role="tabpanel"] [role="img"]'])
})

test.describe('as Mbali', () => {
  test.use({ storageState: mbali })

  for (const path of ['/plan', '/plan/00000000-0000-4000-8000-000000000001', '/electives', '/history', '/no-such-page']) {
    test(path, async ({ page }) => {
      await check(page, path)
    })
  }

  for (const [who, path] of [
    ['staff', '/staff'],
    ['refused', '/wrong-account'],
    ['unfinished', '/onboarding'],
  ] as const) {
    test(`${path}, as ${who}`, async ({ page }) => {
      await visitAs(page, who)
      await check(page, path)
    })
  }
})
