// The accessibility check: axe-core's rules for WCAG 2.0 to 2.2 at levels A and AA, as the design
// audit ran them. The bar is zero violations.
import AxeBuilder from '@axe-core/playwright'
import { expect, type Page } from '@playwright/test'

export async function expectNoAxeViolations(page: Page): Promise<void> {
  const { violations } = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze()
  // Each rule broken, and where, so a failure says what to fix
  expect(violations.map(({ id, nodes }) => ({ id, where: nodes.map((node) => node.target.join(' ')) }))).toEqual([])
}
