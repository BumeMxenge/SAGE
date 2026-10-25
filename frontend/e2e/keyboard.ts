// The keyboard walk: Tab from the top of the page until focus leaves it, checking that every stop shows
// SAGE's focus ring, a solid outline at least 2 px wide, and that no other ring is on screen, as on a
// box around the stop that React Aria marks too. Two components draw it beside the focused
// element rather than on it: the chat box rings its wrapper, and the checkbox its box, beside its
// hidden input in the same label. So the ring may sit on the element, around it, inside it or in its
// label. It returns each stop's role and name, as the accessibility tree gives them, in order, for a
// spec to check the order.
import { expect, type JSHandle, type Page } from '@playwright/test'

export async function walkKeyboard(page: Page): Promise<string[]> {
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur()
  })
  const stops: string[] = []
  let first: JSHandle | null = null
  for (;;) {
    await page.keyboard.press('Tab')
    const focused = await page.evaluateHandle(() => document.activeElement)
    const found = await page.evaluate(
      ([element, start]) => {
        // Focus has left the page, or come round to the first stop
        if (!(element instanceof Element) || element === document.body || element === start) return null
        const showsRing = (candidate: Element) => {
          const { outlineStyle, outlineWidth } = getComputedStyle(candidate)
          return outlineStyle === 'solid' && parseFloat(outlineWidth) >= 2
        }
        const around: Element[] = []
        for (let parent = element.parentElement; parent; parent = parent.parentElement) around.push(parent)
        // A checkbox's input is hidden inside its label, and the box beside it shows the ring
        const label = element.closest('label')
        const near = [element, ...around, ...element.querySelectorAll('*'), ...(label ? label.querySelectorAll('*') : [])]
        // A visually hidden element, such as that input, can't show a ring
        const rings = [...document.querySelectorAll('*')].filter((candidate) => {
          const { width, height } = candidate.getBoundingClientRect()
          return width > 1 && height > 1 && showsRing(candidate)
        })
        return { ringed: near.some(showsRing), rings: rings.length }
      },
      [focused, first] as const,
    )
    if (found === null) return stops
    first ??= focused
    // Such as: button "Continue with UCT Email"
    const [stop] = (await page.locator(':focus').ariaSnapshot()).replace(/^- /, '').split('\n')
    expect(found.ringed, `the focus ring on ${stop}`).toBe(true)
    expect(found.rings, `rings on screen at ${stop}`).toBe(1)
    stops.push(stop)
    // A page has far fewer stops than this, so more means focus is trapped
    expect(stops.length, 'stops before focus leaves the page').toBeLessThan(200)
  }
}
