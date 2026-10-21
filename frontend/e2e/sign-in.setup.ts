// Signs Mbali in once per run, with the link make sign-in prints, and saves her browser's sign-in for
// the checks
import { test as setup } from '@playwright/test'
import { mbali, signInLink } from './visitors.ts'

setup('sign Mbali in', async ({ page }) => {
  // make sign-in alone takes 15 to 30 s, as it asks local Supabase for its keys first, and the test's
  // time counts it
  setup.setTimeout(90_000)
  await page.goto(signInLink('sign-in'))
  // Home is /plan, which opens her first plan at its own address
  await page.waitForURL(/\/plan\/[\w-]+$/)
  await page.context().storageState({ path: mbali })
})
