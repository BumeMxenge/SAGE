// The frame around the student's pages, as Mbali: the sidebar's links, folding and the account menu,
// then parity against the planner prototype in both themes, at rest and on hover. routes.spec.ts
// already runs axe and the keyboard walk on every page with the sidebar open, so here they run on the
// rail and the open menu.
import { expect, type Locator, type Page, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../e2e/axe.ts'
import { walkKeyboard } from '../../e2e/keyboard.ts'
import { type ParityCase, parity, type Theme } from '../../e2e/parity.ts'
import { settled } from '../../e2e/settled.ts'
import { mbali } from '../../e2e/visitors.ts'

test.use({ storageState: mbali })

const sidebar = (page: Page) => page.getByRole('banner')
// Mbali never has a name from Microsoft, so her account shows her student number
const account = (page: Page) => sidebar(page).getByRole('button', { name: /DLMMBA999/ })

// The account waits for the name lookup, so the sidebar is whole once it shows
async function opened(page: Page): Promise<void> {
  await account(page).waitFor()
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
  for (const [name, path] of [
    ['Explore Electives', '/electives'],
    ['Course History', '/history'],
    ['Plan', '/plan'],
  ]) {
    await sidebar(page).getByRole('link', { name, exact: true }).click()
    await page.waitForURL(`**${path}`)
    await expect(page.getByRole('heading', { level: 1, name })).toBeVisible()
    await expect(current).toHaveText(name)
  }
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

test('Sign Out leaves nothing of the student in the browser', async ({ page }) => {
  // Supabase's sign-out ends every session an account has, and local Supabase checks every token
  // with its Auth server, so a real one would sign out every other check running as Mbali. Answered
  // here, the browser's side runs as it would: supabase-js drops the session, and SAGE forgets the
  // rest. Without the header, the browser would refuse the answer as a failed request.
  let asked = false
  await page.route('**/auth/v1/logout*', async (route) => {
    asked = true
    await route.fulfill({ status: 204, headers: { 'Access-Control-Allow-Origin': '*' } })
  })
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
  await named.click()
  await page.getByRole('menuitem', { name: 'Sign Out' }).click()
  await page.waitForURL('**/sign-in')
  expect(asked).toBe(true)
  const kept = await page.evaluate(() => Object.keys(localStorage).filter((key) => key.startsWith('sage-name-')))
  expect(kept).toEqual([])
  await page.goto('/plan')
  await page.waitForURL('**/sign-in')
})

test('the rail passes axe, and the keyboard walks it in order, each stop ringed', async ({ page }) => {
  await page.goto('/plan')
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
