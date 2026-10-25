// The accessibility check: axe-core's rules for WCAG 2.0 to 2.2 at levels A and AA, as the design
// audit ran them. The bar is zero violations. A spec may name elements axe leaves out, each with its
// reason beside it. It waits for whatever is fading in to arrive, as axe counts half-faded text as too
// faint.
import AxeBuilder from '@axe-core/playwright'
import { expect, type Page } from '@playwright/test'
import { settled } from './settled.ts'

export async function expectNoAxeViolations(page: Page, leaveOut: string[] = []): Promise<void> {
  await settled(page)
  const axe = new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
  for (const selector of leaveOut) axe.exclude(selector)
  const { violations } = await axe.analyze()
  // Each rule broken, and where, so a failure says what to fix
  expect(violations.map(({ id, nodes }) => ({ id, where: nodes.map((node) => node.target.join(' ')) }))).toEqual([])
}
