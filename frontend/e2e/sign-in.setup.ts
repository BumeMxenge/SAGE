// Signs Mbali in once per run, with the link make sign-in prints, and saves her browser's sign-in for
// the checks
import { test as setup } from '@playwright/test'
import { mbali, signInLink } from './visitors.ts'

setup('sign Mbali in', async ({ page }) => {
  await page.goto(signInLink('sign-in'))
  await page.waitForURL('**/plan')
  await page.context().storageState({ path: mbali })
})
