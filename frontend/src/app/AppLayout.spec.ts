// The frame around the student's pages, as Mbali: the sidebar's links, folding and the account menu,
// then parity against the planner prototype in both themes, at rest and on hover. routes.spec.ts
// already runs axe and the keyboard walk on every page with the sidebar open, so here they run on the
// rail and the open menu. While the first load's guard waits on GET /v1/me, held, the frame shows,
// the account as a skeleton and the address's skeleton beside it, and no page opens until the guard
// lets it, with axe and a photograph beside what it turns into, and the frame sends no read of its own
// before the guard decides, so a signed-out visitor asks the API nothing. Sign Out leaves asking the
// API nothing and logging no error, and whoever signs in next on the same page sees nothing of hers.
// Explore Electives shows only to a student whose plans have a complementary slot. Mbali's have none,
// so her set is answered as if they had one, as the prototype draws all three links, except where a
// check says otherwise: with her own set, the link's skeleton holds its row and then goes, and if the
// read fails it goes and the link stays hidden.
import { expect, type Locator, type Page, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../e2e/axe.ts'
import { walkKeyboard } from '../../e2e/keyboard.ts'
import {
  forgetSeen,
  hold,
  loading,
  photographArrival,
  read,
  refusal,
  seenLoading,
  settledArrival,
  skeletons,
  watchLoading,
} from '../../e2e/loading.ts'
import { type ParityCase, parity, type Theme } from '../../e2e/parity.ts'
import { settled } from '../../e2e/settled.ts'
import { mbali, signInLink, visitAs, withSlot } from '../../e2e/visitors.ts'

test.use({ storageState: mbali })

test.beforeEach(async ({ page }) => {
  await withSlot(page)
})

const sidebar = (page: Page) => page.getByRole('banner')
const navigation = (page: Page) => sidebar(page).getByRole('navigation', { name: 'Main' })

// Where an element sits on the screen
async function box(element: Locator) {
  const found = await element.boundingBox()
  if (!found) throw new Error(`${element.toString()} isn't on screen`)
  return found
}
// Mbali never has a name from Microsoft, so her account shows her student number
const account = (page: Page) => sidebar(page).getByRole('button', { name: /DLMMBA999/ })

// The account waits for the name lookup, so the sidebar is whole once it shows
// The page beside it arrives too, and fades in, before the checks read the window
// Every request the page makes to the API from now on, by its path
function apiReads(page: Page): string[] {
  const paths: string[] = []
  page.on('request', (request) => {
    const { pathname } = new URL(request.url())
    if (pathname.startsWith('/v1/')) paths.push(pathname)
  })
  return paths
}

async function opened(page: Page): Promise<void> {
  await account(page).waitFor()
  await settledArrival(page)
  await settled(page)
}

async function collapse(page: Page): Promise<void> {
  await opened(page)
  await page.getByRole('button', { name: 'Collapse Sidebar' }).click()
  await settled(page)
}

async function openMenu(page: Page): Promise<void> {
  await opened(page)
  await account(page).click()
  await settled(page)
}

test('each link opens its page, and only that link is current, a plan of its own included', async ({ page }) => {
  await page.goto('/plan/00000000-0000-4000-8000-000000000001')
  const current = sidebar(page).locator('[aria-current="page"]')
  await expect(current).toHaveText('Plan')
  for (const [name, address] of [
    ['Explore Electives', '**/electives'],
    ['Course History', '**/history'],
    // Plan opens her first plan, at its own address
    ['Plan', /\/plan\/[\w-]+$/],
  ] as const) {
    await sidebar(page).getByRole('link', { name, exact: true }).click()
    await page.waitForURL(address)
    await expect(page.getByRole('heading', { level: 1, name })).toBeVisible()
    await expect(current).toHaveText(name)
  }
})

test("with no complementary slot in her plans, Explore Electives' row waits as a skeleton the size of a link, then goes, and Course History moves up once", async ({
  page,
}) => {
  // Her own set, which has no slot
  await page.unroute('**/v1/plans')
  const set = await hold(page, read('/v1/plans'))
  await page.goto('/history')
  const history = navigation(page).getByRole('link', { name: 'Course History' })
  await account(page).waitFor()
  const skeleton = skeletons(navigation(page))
  await expect(skeleton).toHaveCount(1)
  await expect(navigation(page).getByRole('link')).toHaveText(['Plan', 'Course History'])
  expect((await box(skeleton)).height).toBe((await box(navigation(page).getByRole('link', { name: 'Plan' }))).height)
  await expectNoAxeViolations(page)
  const waiting = await box(history)
  await set.release()
  await expect(skeleton).toHaveCount(0)
  await expect(navigation(page).getByRole('link')).toHaveText(['Plan', 'Course History'])
  expect((await box(history)).y).toBeLessThan(waiting.y)
})

test("if her plans can't be read, Explore Electives' skeleton goes and the link stays hidden", async ({ page }) => {
  const set = await hold(page, read('/v1/plans'))
  await page.goto('/history')
  await account(page).waitFor()
  await set.refuse(refusal('internal_error', 500))
  // A failed read is tried again three times, 1, 2 and 4 s apart
  await expect(skeletons(navigation(page))).toHaveCount(0, { timeout: 15_000 })
  await expect(navigation(page).getByRole('link')).toHaveText(['Plan', 'Course History'])
})

test('folding and opening by keyboard leaves focus on the toggle that replaced the one pressed', async ({ page }) => {
  await page.goto('/plan')
  await opened(page)
  await page.getByRole('button', { name: 'Collapse Sidebar' }).focus()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('button', { name: 'Open Sidebar' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('button', { name: 'Collapse Sidebar' })).toBeFocused()
})

test('the sidebar is open from 1100 px wide and folded below, as a page opens and as the window changes', async ({ page }) => {
  const folded = page.getByRole('button', { name: 'Open Sidebar' })
  const open = page.getByRole('button', { name: 'Collapse Sidebar' })
  await page.setViewportSize({ width: 1100, height: 820 })
  await page.goto('/plan')
  await expect(open).toBeVisible()
  await page.setViewportSize({ width: 1099, height: 820 })
  await expect(folded).toBeVisible()
  await page.reload()
  await expect(folded).toBeVisible()
  await page.setViewportSize({ width: 1100, height: 820 })
  await expect(open).toBeVisible()
})

test('choosing an appearance in the account menu changes the theme', async ({ page }, testInfo) => {
  // The run's own theme would pass with a menu that did nothing, so this chooses the other one
  const other = testInfo.project.name === 'dark' ? 'Light' : 'Dark'
  await page.goto('/plan')
  await openMenu(page)
  await page.getByRole('menuitemradio', { name: other }).click()
  await expect(page.locator('html')).toHaveAttribute('data-theme', other.toLowerCase())
})

test("while the first load's guard asks who is visiting, the frame shows with the address's skeleton, and the page opens only once it has decided", async ({
  page,
}, testInfo) => {
  await page.goto('/plan')
  await page.waitForURL(/\/plan\/[\w-]+$/)
  // Her plan has arrived, so no read of this first page is still on its way when the count starts
  await page.getByRole('button', { name: /^Power, Control & Robotics/ }).waitFor()
  const address = page.url()
  const me = await hold(page, read('/v1/me'))
  const asked = apiReads(page)
  await page.reload()
  await expect(sidebar(page).getByRole('link', { name: 'Course History', exact: true })).toBeVisible()
  await expect(loading(page, 'Loading your account…')).toBeAttached()
  await expect(skeletons(sidebar(page)).first()).toBeVisible()
  await expect(loading(page, 'Loading your plan…')).toBeAttached()
  await expect(skeletons(page.getByRole('main')).first()).toBeVisible()
  await expect(page.getByRole('button', { name: 'Open Assistant' })).toBeVisible()
  // No page has opened: the plan's own controls wait for the guard
  await expect(page.getByRole('button', { name: /^Power, Control & Robotics/ })).toHaveCount(0)
  expect(page.url()).toBe(address)
  // The frame only watches reads, so nothing but the guard's own goes out before it decides. In
  // development StrictMode closes and opens the frame once, which cancels that read and asks again.
  expect(new Set(asked)).toEqual(new Set(['/v1/me']))
  await expectNoAxeViolations(page)
  await photographArrival(page, testInfo, 'first-load', () => me.release())
  await expect(account(page)).toBeVisible()
  await expect(page.getByRole('button', { name: /^Power, Control & Robotics/ })).toBeVisible()
})

test("a signed-out visitor at a plan's address goes to /sign-in having asked the API nothing", async ({ browser }) => {
  // The file's options, Mbali's session among them, reach a context made here too, so it's emptied
  const visitor = await browser.newContext({ storageState: { cookies: [], origins: [] } })
  const page = await visitor.newPage()
  const asked = apiReads(page)
  await page.goto('/plan/00000000-0000-4000-8000-000000000001')
  await page.waitForURL('**/sign-in')
  await page.getByRole('heading', { level: 1 }).waitFor()
  expect(asked).toEqual([])
  await visitor.close()
})

// The app's Supabase client, as much of it as the next sign-in uses
type SupabaseModule = {
  supabase: { auth: { verifyOtp: (link: { token_hash: string; type: 'magiclink' }) => Promise<unknown> } }
}

test('Sign Out asks the API nothing on its way out, and leaves nothing of the student for whoever signs in next', async ({
  page,
}) => {
  // make sign-in's link for the next sign-in takes 15 to 30 s
  test.setTimeout(90_000)
  // Supabase's sign-out ends every session an account has, and local Supabase checks every token
  // with its Auth server, so a real one would sign out every other check running as Mbali. Answered
  // here, the browser's side runs as it would: supabase-js drops the session, and SAGE forgets the
  // rest. Without the header, the browser would refuse the answer as a failed request.
  let loggedOut = false
  await page.route('**/auth/v1/logout*', async (route) => {
    loggedOut = true
    await route.fulfill({ status: 204, headers: { 'Access-Control-Allow-Origin': '*' } })
  })
  await watchLoading(page)
  await page.goto('/plan')
  await opened(page)
  // A made-up name, kept as the sign-in keeps one from Microsoft
  await page.evaluate(() => {
    for (const key of Object.keys(localStorage).filter((stored) => stored.endsWith('-auth-token'))) {
      const { user } = JSON.parse(localStorage.getItem(key) ?? '{}') as { user: { id: string } }
      localStorage.setItem(`sage-name-${user.id}`, JSON.stringify({ givenName: 'Mbali', surname: 'Dlamini' }))
    }
  })
  await page.reload()
  const named = sidebar(page).getByRole('button', { name: /Mbali Dlamini/ })
  await expect(named).toContainText('MD')
  await page.getByRole('button', { name: /^Power, Control & Robotics/ }).waitFor()
  await settled(page)
  await forgetSeen(page)
  const asked = apiReads(page)
  const errors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await named.click()
  await page.getByRole('menuitem', { name: 'Sign Out' }).click()
  await page.waitForURL('**/sign-in')
  await page.getByRole('heading', { level: 1 }).waitFor()
  expect(loggedOut).toBe(true)
  // The cache empties only once her pages have closed, so none of them asks for its reads again,
  // unsigned, and the console logs no 401, and no skeleton shows for the reads it emptied
  expect([...asked]).toEqual([])
  expect(errors).toEqual([])
  expect((await seenLoading(page)).skeletons).toBe(0)
  const kept = await page.evaluate(() => Object.keys(localStorage).filter((key) => key.startsWith('sage-name-')))
  expect(kept).toEqual([])
  // Her session has gone: her plans send whoever asks to sign in. On this page, not a reload, so what
  // Sign Out left in its memory stays for the next sign-in to find.
  await page.evaluate(() => {
    history.pushState(null, '', '/plan')
    dispatchEvent(new PopStateEvent('popstate'))
  })
  await page.waitForURL('**/sign-in')

  // The next person signs in on this page: a made-up student who hasn't finished setup. Anything of
  // Mbali's left in the page, such as her account in the cache, would send them to her plans.
  await visitAs(page, 'unfinished')
  const tokenHash = new URL(signInLink('sign-in')).searchParams.get('token_hash')
  if (!tokenHash) throw new Error("make sign-in's link carries no token")
  await page.evaluate(async (hash) => {
    // SAGE signs a link in only as a page loads, so the check does it through the app's own client,
    // as the dev server serves it, then comes back to /, as every sign-in does
    const client = '/src/lib/supabase.ts'
    const { supabase } = (await import(client)) as SupabaseModule
    await supabase.auth.verifyOtp({ token_hash: hash, type: 'magiclink' })
    history.pushState(null, '', '/')
    dispatchEvent(new PopStateEvent('popstate'))
  }, tokenHash)
  await page.waitForURL('**/onboarding')
  await page.getByRole('heading', { level: 1 }).waitFor()
  await expect(page.getByText(/DLMMBA999|Mbali|Power, Control & Robotics/)).toHaveCount(0)
})

test('the rail passes axe, and the keyboard walks it in order, each stop ringed', async ({ page }) => {
  // Course History has nothing to press, so the rail's stops are the page's only ones
  await page.goto('/history')
  await collapse(page)
  await expectNoAxeViolations(page)
  // Focus moved to Open Sidebar, and Tab would go on from there, so the walk starts from the corner
  await page.mouse.click(0, 0)
  const stops = await walkKeyboard(page)
  expect(stops).toEqual([
    'button "Open Sidebar"',
    'link "Plan":',
    'link "Explore Electives":',
    'link "Course History":',
    'button "DLMMBA999 dlmmba999@myuct.ac.za"',
  ])
})

test('the account menu passes axe, the arrow keys move through it, and Escape returns to the account', async ({ page }) => {
  await page.goto('/plan')
  await opened(page)
  await account(page).focus()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('menuitemradio', { name: 'Match System' })).toBeFocused()
  await page.keyboard.press('ArrowDown')
  await expect(page.getByRole('menuitemradio', { name: 'Light' })).toBeFocused()
  await settled(page)
  await expectNoAxeViolations(page)
  await page.keyboard.press('Escape')
  await expect(page.getByRole('menu')).toHaveCount(0)
  await expect(account(page)).toBeFocused()
})

// Parity. The prototype opens at the empty plan with its sidebar open, and reads its theme from its
// address. It draws the open sidebar over its rail and hides the one not in use from screen readers
// only, so each control is looked up in the panel on screen.
async function prototypeIn(page: Page, theme: Theme): Promise<void> {
  if (theme === 'dark') await page.goto(`${page.url()}?theme=dark`)
  await settled(page)
}

const openPanel = (page: Page) => page.locator('aside[aria-hidden="false"]')
const railPanel = (page: Page) => page.locator('aside:not([aria-hidden])')
// The box that narrows to fold the sidebar, which holds both panels and the menu
const designedSidebar = (page: Page) => page.locator('aside[aria-hidden]').locator('..')

async function collapsePrototype(page: Page): Promise<void> {
  await openPanel(page).getByRole('button', { name: 'Collapse panel' }).click()
  await page.mouse.move(640, 410)
  await settled(page)
}

async function openPrototypeMenu(page: Page): Promise<void> {
  await openPanel(page).getByRole('button', { name: /Mbali Dlamini/ }).click()
  await settled(page)
}

type Step = (page: Page) => Promise<void>
const rest: Step = async () => undefined

// The sidebar in one state, the prototype's beside React's
function state(name: string, designed: Step, built: Step): ParityCase {
  return {
    name,
    prototype: 'registration-planner',
    reach: async (page, theme) => {
      await prototypeIn(page, theme)
      await designed(page)
      return designedSidebar(page)
    },
    react: { path: '/plan', reach: built, element: sidebar },
  }
}

// One control, at rest and on hover, in a state of the sidebar
function control(
  name: string,
  steps: { designed: Step; built: Step },
  designed: (page: Page) => Locator,
  built: (page: Page) => Locator,
): ParityCase {
  return {
    name,
    prototype: 'registration-planner',
    reach: async (page, theme) => {
      await prototypeIn(page, theme)
      await steps.designed(page)
      return designed(page)
    },
    react: { path: '/plan', reach: steps.built, element: built },
    hover: true,
  }
}

const atRest = { designed: rest, built: opened }
const folded = { designed: collapsePrototype, built: collapse }
const withMenu = { designed: openPrototypeMenu, built: openMenu }

parity('shell', [
  state('sidebar', rest, opened),
  state('rail', collapsePrototype, collapse),
  state('account-menu', openPrototypeMenu, openMenu),
  control(
    'nav-item',
    atRest,
    (page) => openPanel(page).getByRole('button', { name: 'Explore electives' }),
    (page) => page.getByRole('link', { name: 'Explore Electives' }),
  ),
  control(
    'collapse-button',
    atRest,
    (page) => openPanel(page).getByRole('button', { name: 'Collapse panel' }),
    (page) => page.getByRole('button', { name: 'Collapse Sidebar' }),
  ),
  control('account-button', atRest, (page) => openPanel(page).getByRole('button', { name: /Mbali Dlamini/ }), account),
  control(
    'rail-item',
    folded,
    (page) => railPanel(page).getByRole('button', { name: 'Course history' }),
    (page) => page.getByRole('link', { name: 'Course History' }),
  ),
  control(
    'rail-open',
    folded,
    (page) => page.locator('[data-tip="Open sidebar"]'),
    (page) => page.getByRole('button', { name: 'Open Sidebar' }),
  ),
  control('rail-account', folded, (page) => railPanel(page).getByRole('button', { name: 'Account' }), account),
  control(
    'menu-item',
    withMenu,
    (page) => openPanel(page).getByRole('button', { name: /Switch to/ }),
    (page) => page.getByRole('menuitemradio', { name: 'Dark' }),
  ),
  control(
    'sign-out',
    withMenu,
    (page) => openPanel(page).getByRole('button', { name: 'Log out' }),
    (page) => page.getByRole('menuitem', { name: 'Sign Out' }),
  ),
])
