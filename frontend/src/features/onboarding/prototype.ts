// Helpers for the onboarding specs' parity cases, which drive the prototypes in docs/prototypes
import type { Page } from '@playwright/test'

// Opens one of the onboarding prototype's states through its own switcher, then hides the switcher,
// which floats over every state, so it stays out of the photographs and out of the way of clicks
export async function showState(page: Page, state: string): Promise<void> {
  await page.getByRole('button', { name: state, exact: true }).click()
  await page
    .getByText('STATES', { exact: true })
    .locator('..')
    .evaluate((switcher) => {
      switcher.style.visibility = 'hidden'
    })
}
