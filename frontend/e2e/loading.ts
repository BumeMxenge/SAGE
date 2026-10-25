// The loading states in the UI checks. A check holds a read on its way, so its skeleton stays on
// screen until the check lets the read go, or refuses it. A skeleton is found by its class, which the
// dev server names after Skeleton's stylesheet, and a page's status line by its words. A watch set up
// before the page opens counts every skeleton and status line that appears, and every fade-in, for the
// checks that none may. Each skeleton is photographed beside the page it turns into, at the window's
// size, in the run's theme, into frontend/parity/skeletons/, which git ignores.
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { expect, type Locator, type Page, type Route, type TestInfo } from '@playwright/test'
import type { components } from '../src/lib/api-types.ts'
import { sheet } from './parity.ts'
import { settled } from './settled.ts'

type Problem = components['schemas']['Problem']

// The API is on another port, so each answer allows this page's origin, as the backend's CORS does
const allowed = { 'Access-Control-Allow-Origin': '*' }

export type Hold = {
  // Lets every held request go on, and those after it
  release: () => Promise<void>
  // Answers every held request, and every later one, with this refusal, so the read stays failed
  // when the page asks again, as it does for a failed read on the window's next focus
  refuse: (problem: Problem) => Promise<void>
}

// Holds every request the page makes with this method to a matching address, until the check lets
// them go or refuses them. A held request the page has since cancelled, as React's StrictMode does
// with a read it starts twice in development, is already gone.
export async function hold(page: Page, matches: (url: URL) => boolean, method = 'GET'): Promise<Hold> {
  const held: Route[] = []
  const handler = async (route: Route) => {
    if (route.request().method() !== method) return route.fallback()
    held.push(route)
  }
  await page.route(matches, handler)
  const settle = async (answer: (route: Route) => Promise<void>) => {
    await page.unroute(matches, handler)
    for (const route of held.splice(0)) {
      await answer(route).catch((error: unknown) => {
        if (!(error instanceof Error) || !error.message.includes('already handled')) throw error
      })
    }
  }
  return {
    release: () => settle((route) => route.fallback()),
    refuse: async (problem) => {
      const answer = (route: Route) =>
        route.request().method() === method
          ? route.fulfill({ status: problem.status, contentType: 'application/problem+json', json: problem, headers: allowed })
          : route.fallback()
      // Refusing before the hold lets go, so no request slips through to the API between the two
      await page.route(matches, answer)
      await settle(answer)
    },
  }
}

export const refusal = (code: Problem['code'], status: number): Problem => ({
  type: 'about:blank',
  title: 'Made Up',
  status,
  detail: 'A made-up refusal.',
  code,
})

// The address an API read goes to
export const read = (path: string) => (url: URL) => url.pathname === path

export const skeletons = (within: Page | Locator) => within.locator('[class*="_skeleton_"]')

// A status line saying what's loading, such as "Loading your plan…"
export const loading = (page: Page, words?: string) => page.locator('output', { hasText: words ?? /^Loading / })

type Seen = { skeletons: number; fades: number }

// Counts, from before the page opens, every skeleton or loading status line put on the page and every
// content that fades in, until forgetSeen starts the count again
export async function watchLoading(page: Page): Promise<void> {
  await page.addInitScript(() => {
    const seen = { skeletons: 0, fades: 0 }
    Object.assign(window, { loadingSeen: seen })
    const skeleton = '[class*="_skeleton_"]'
    const isLoading = (node: Node) =>
      node instanceof Element &&
      (node.matches(skeleton) ||
        node.querySelector(skeleton) !== null ||
        [node, ...node.querySelectorAll('output')].some(
          (element) => element.tagName === 'OUTPUT' && element.textContent.startsWith('Loading '),
        ))
    new MutationObserver((records) => {
      for (const record of records) seen.skeletons += [...record.addedNodes].filter(isLoading).length
    }).observe(document, { childList: true, subtree: true })
    document.addEventListener('animationstart', (event) => {
      if (event.animationName.includes('_arrive_')) seen.fades += 1
    })
  })
}

export const seenLoading = (page: Page) => page.evaluate(() => (window as unknown as { loadingSeen: Seen }).loadingSeen)

export async function forgetSeen(page: Page): Promise<void> {
  await page.evaluate(() => Object.assign((window as unknown as { loadingSeen: Seen }).loadingSeen, { skeletons: 0, fades: 0 }))
}

// The window as it is, with the mouse off the page's controls, once whatever is moving in has arrived
async function windowShot(page: Page): Promise<Buffer> {
  await page.mouse.move(0, 0)
  await settled(page)
  return page.screenshot()
}

// Photographs the skeleton on screen now, then, once arrive has let its read go and the page has
// arrived, the page it turns into, and sets the two side by side
export async function photographArrival(
  page: Page,
  testInfo: TestInfo,
  name: string,
  arrive: () => Promise<void>,
): Promise<void> {
  const waiting = await windowShot(page)
  await arrive()
  await settledArrival(page)
  const arrived = await windowShot(page)
  const folder = join(import.meta.dirname, '..', 'parity', 'skeletons')
  mkdirSync(folder, { recursive: true })
  const theme = testInfo.project.name === 'dark' ? 'dark' : 'light'
  const browser = page.context().browser()
  if (!browser) throw new Error('The page has no browser to lay the photographs out in')
  await sheet(browser, join(folder, `${name}-${theme}.png`), [
    ['Skeleton', waiting],
    ['Arrived', arrived],
  ])
}

// No skeleton or loading status line left on the page. A read can take several seconds when a full run
// loads the machine, so it waits longer than Playwright's 5 s.
export async function settledArrival(page: Page): Promise<void> {
  await expect(loading(page)).toHaveCount(0, { timeout: 15_000 })
  await expect(skeletons(page)).toHaveCount(0, { timeout: 15_000 })
}
