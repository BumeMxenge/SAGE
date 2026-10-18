// Every page in the route table, opened by the visitor it's for, has no axe violations and a clean
// keyboard walk, in light and dark. Staff, an account from outside UCT and a student who hasn't
// finished setup are Mbali's session with a made-up answer from GET /v1/me, so no check resets a real
// account.
import { expect, type Page, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../e2e/axe.ts'
import { walkKeyboard } from '../../e2e/keyboard.ts'
import { mbali, visitAs } from '../../e2e/visitors.ts'
import { pageNames } from '../lib/copy.ts'

// The page opens for its visitor, the guard lets them stay, and it passes both checks
async function check(page: Page, path: string, heading: string): Promise<void> {
  await page.goto(path)
  await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible()
  expect(new URL(page.url()).pathname).toBe(path)
  await expectNoAxeViolations(page)
  await walkKeyboard(page)
}

test('/sign-in, signed out', async ({ page }) => {
  await check(page, '/sign-in', pageNames.signIn)
})

test.describe('as Mbali', () => {
  test.use({ storageState: mbali })

  for (const [path, heading] of [
    ['/plan', pageNames.plan],
    ['/plan/00000000-0000-4000-8000-000000000001', pageNames.plan],
    ['/electives', pageNames.electives],
    ['/history', pageNames.history],
    ['/no-such-page', pageNames.notFound],
  ]) {
    test(path, async ({ page }) => {
      await check(page, path, heading)
    })
  }

  for (const [who, path, heading] of [
    ['staff', '/staff', pageNames.staff],
    ['refused', '/wrong-account', pageNames.wrongAccount],
    ['unfinished', '/onboarding', pageNames.onboarding],
  ] as const) {
    test(`${path}, as ${who}`, async ({ page }) => {
      await visitAs(page, who)
      await check(page, path, heading)
    })
  }
})
