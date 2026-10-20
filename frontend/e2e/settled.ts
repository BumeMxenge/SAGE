// Waits until whatever is arriving on the page, in a prototype or in React, has arrived: a step
// sliding in, a sidebar folding away, a menu fading up. A looping animation, such as a loader's, never
// ends, so it doesn't count.
import type { Page } from '@playwright/test'

export async function settled(page: Page): Promise<void> {
  await page.waitForFunction(() =>
    document
      .getAnimations()
      .every((animation) => animation.playState !== 'running' || animation.effect?.getComputedTiming().iterations === Infinity),
  )
}
