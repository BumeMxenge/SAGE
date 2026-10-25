// The parity script. Each case drives a prototype in docs/prototypes/ to a state through its own
// controls, opens the same state in React, and writes the two side by side, at rest and on hover, in
// the run's theme, into frontend/parity/<feature>/, which git ignores. The images are for review by eye
// on the Mac, as screenshots differ between operating systems. Where a prototype has no design for a
// theme, as onboarding has none in dark, the image shows React alone.
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { type Browser, type Locator, type Page, test } from '@playwright/test'

export type Theme = 'light' | 'dark'

export type ParityCase = {
  name: string // the image's name, such as sign-in-button
  prototype: 'onboarding' | 'registration-planner' | 'error-states' | 'loading-states'
  // The prototype's own controls, from the page as it opens, to the state in this theme. It returns
  // the element to photograph, or null where the prototype has no design for the theme.
  reach: (page: Page, theme: Theme) => Promise<Locator | null>
  // The React page's address, the clicks from there to a state that has no address of its own, such
  // as an onboarding step, and the element to photograph
  react: { path: string; reach?: (page: Page) => Promise<void>; element: (page: Page) => Locator }
  hover?: boolean
}

const prototypes = join(import.meta.dirname, '..', '..', 'docs', 'prototypes')
const images = join(import.meta.dirname, '..', 'parity')

// Registers one test for each case, which runs in each theme's project
export function parity(feature: string, cases: ParityCase[]): void {
  for (const { name, prototype, reach, react, hover } of cases) {
    test(`parity: ${name}`, async ({ browser, page }, testInfo) => {
      const theme: Theme = testInfo.project.name === 'dark' ? 'dark' : 'light'
      // The prototype opens from disk, with every request to the network refused, so all it shows is
      // its own
      const offline = await browser.newContext({ viewport: { width: 1280, height: 820 }, colorScheme: theme })
      await offline.route(/^https?:/, (route) => route.abort())
      const designedPage = await offline.newPage()
      await designedPage.goto(pathToFileURL(join(prototypes, `${prototype}.html`)).href)
      const designed = await reach(designedPage, theme)
      await page.goto(react.path)
      await react.reach?.(page)
      const built = react.element(page)

      const folder = join(images, feature)
      mkdirSync(folder, { recursive: true })
      await sideBySide(browser, join(folder, `${name}-${theme}.png`), designed, built)
      if (hover) {
        await designed?.hover()
        await built.hover()
        await sideBySide(browser, join(folder, `${name}-${theme}-hover.png`), designed, built)
      }
      await offline.close()
    })
  }
}

// An element with 16 px of the page around it, so its shadow and its surroundings show too
async function photograph(element: Locator): Promise<Buffer> {
  await element.scrollIntoViewIfNeeded()
  const box = await element.boundingBox()
  if (!box) throw new Error(`Nothing to photograph: ${element.toString()} isn't on screen`)
  const x = Math.max(0, box.x - 16)
  const y = Math.max(0, box.y - 16)
  return element.page().screenshot({ clip: { x, y, width: box.x + box.width + 16 - x, height: box.y + box.height + 16 - y } })
}

// The two photographs on one image, labelled, the prototype's first
async function sideBySide(browser: Browser, path: string, designed: Locator | null, built: Locator): Promise<void> {
  const shots = [...(designed ? [['Prototype', await photograph(designed)] as const] : []), ['React', await photograph(built)] as const]
  await sheet(browser, path, shots)
}

// Labelled photographs side by side on one image, in the order given
export async function sheet(browser: Browser, path: string, shots: (readonly [string, Buffer])[]): Promise<void> {
  const figures = shots
    .map(([label, png]) => `<figure><figcaption>${label}</figcaption><img src="data:image/png;base64,${png.toString('base64')}"></figure>`)
    .join('')
  const page = await browser.newPage()
  await page.setContent(
    `<style>body { margin: 0; } main { display: inline-flex; gap: 32px; align-items: flex-start; padding: 16px; font: 14px system-ui; background: #fff; } figure { margin: 0; } figcaption { margin-bottom: 8px; }</style><main>${figures}</main>`,
  )
  await page.locator('main').screenshot({ path })
  await page.close()
}
