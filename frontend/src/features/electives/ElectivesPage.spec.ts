// Explore Electives as a made-up student with a complementary slot, on made-up answers from the API.
// Every /v1 request is answered here, and a catch-all refuses any other and fails the check, so no
// heart reaches the database every worktree shares. Mbali's session signs the browser in.
//
// It checks that hearting a course offered twice sends one PUT for each offering she can heart and
// none for one she can't; that when one of two writes fails, the other is undone, the heart comes
// back and a toast says so; that when the undo fails too, the electives are read again and the card
// shows what saved; that a card with no note has no line at its foot, and one she can't heart shows
// its note and no heart; and that the page passes axe and the keyboard walk in both themes.
import { expect, type Page, type Route, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../../e2e/axe.ts'
import { walkKeyboard } from '../../../e2e/keyboard.ts'
import { mbali } from '../../../e2e/visitors.ts'
import type { components } from '../../lib/api-types.ts'

test.use({ storageState: mbali })

type Me = components['schemas']['Me']
type Electives = components['schemas']['Electives']
type Elective = components['schemas']['Elective']
type Offering = components['schemas']['Offering']
type Problem = components['schemas']['Problem']

// The API is on another port, so each answer allows this page's origin, as the backend's CORS does
const allowed = { 'Access-Control-Allow-Origin': '*' }

// Ziyela, made up, whose plans have a complementary slot
const ziyela: Me = { email: 'ntwziy999@myuct.ac.za', account: 'student', student_number: 'NTWZIY999', onboarding_complete: true }

// Made-up ids for two of her plans
const plan = (number: number) => `00000000-0000-4000-8000-0000000009${String(number).padStart(2, '0')}`

const offering = (code: string, fields: Partial<Offering> = {}): Offering => ({
  code,
  term: code.endsWith('S') ? 'sem2' : 'sem1',
  convener: 'Dr Made Up',
  hearted: false,
  can_heart: true,
  plans: [plan(1), plan(2)],
  ...fields,
})

const card = (name: string, offerings: Offering[], fields: Partial<Elective> = {}): Elective => ({
  codes: offerings.map((each) => each.code),
  name,
  credits: 18,
  summary: `A made-up summary of ${name}.`,
  hearted: false,
  can_heart: offerings.some((each) => each.can_heart),
  note: null,
  offerings,
  ...fields,
})

// The cards the made-up API holds: a course offered twice whose second offering she can't heart, one
// whose two offerings she can, and one she can't heart at all, with the API's note
const marketing = card('Marketing I', [offering('BUS2010F'), offering('BUS2010S', { can_heart: false, plans: [] })], {
  note: 'Only the semester 1 offering fits your plans.',
})
const french = card('French 1A', [offering('SLL1017F'), offering('SLL1017S')])
const greek = card('Greek IA', [offering('SLL1052F', { can_heart: false, plans: [] })], {
  note: "Doesn't fit your plans' timetables.",
})

// What the API answers a write with: saved, or refused as a server error
type Outcome = 'saved' | 'refused'

const refusal: Problem = { type: 'about:blank', title: 'Made Up', status: 500, detail: 'A made-up refusal.', code: 'internal_error' }

// A made-up API for one check. Its hearts are the offerings saved so far, and each write's outcome is
// the check's, by method and code. It records every write and every read of the electives.
async function madeUpApi(page: Page, outcome: (method: string, code: string) => Outcome = () => 'saved') {
  const hearts = new Set<string>()
  const asked = { writes: [] as string[], reads: 0 }
  const electives = (): Electives => {
    const heartedIn = (each: Elective): Elective => {
      const offerings = each.offerings.map((one) => ({ ...one, hearted: hearts.has(one.code) }))
      return { ...each, offerings, hearted: offerings.some((one) => one.hearted) }
    }
    return {
      tabs: [
        { key: 'business', courses: [heartedIn(marketing)] },
        { key: 'languages', courses: [heartedIn(french), heartedIn(greek)] },
      ],
    }
  }
  await page.route('**/v1/me', (route) => route.fulfill({ json: ziyela, headers: allowed }))
  await page.route('**/v1/electives', (route) => {
    asked.reads += 1
    return route.fulfill({ json: electives(), headers: allowed })
  })
  await page.route('**/v1/favourites/*', (route: Route) => {
    const method = route.request().method()
    const code = route.request().url().split('/').at(-1) ?? ''
    asked.writes.push(`${method} ${code}`)
    if (outcome(method, code) === 'refused') {
      return route.fulfill({ status: 500, contentType: 'application/problem+json', json: refusal, headers: allowed })
    }
    if (method === 'PUT') hearts.add(code)
    else hearts.delete(code)
    return route.fulfill({ status: 204, headers: allowed })
  })
  return asked
}

// No check may reach the real API: a /v1 request no check answers is refused, and fails the check
let unanswered: string[] = []
test.beforeEach(async ({ page }) => {
  unanswered = []
  await page.route(
    (url) => url.pathname.startsWith('/v1/'),
    (route) => {
      unanswered.push(`${route.request().method()} ${route.request().url()}`)
      return route.abort()
    },
  )
})
test.afterEach(() => {
  expect(unanswered).toEqual([])
})

const heart = (page: Page, name: string) => page.getByRole('button', { name: `Favourite ${name}` })
const toast = (page: Page) => page.getByText("Your favourite didn't save.")

async function openOn(page: Page, tab: string) {
  await page.goto('/electives')
  await page.getByRole('tab', { name: tab }).click()
}

test('hearting a course offered twice sends one PUT for each offering she can heart', async ({ page }) => {
  const asked = await madeUpApi(page)
  await openOn(page, 'Business & Management')
  await heart(page, 'Marketing I').click()
  await expect(heart(page, 'Marketing I')).toHaveAttribute('aria-pressed', 'true')
  // BUS2010S can't be hearted, so only BUS2010F is written
  expect(asked.writes).toEqual(['PUT BUS2010F'])
})

test('when one of two writes fails, the other is undone, the heart comes back and a toast says so', async ({ page }) => {
  const asked = await madeUpApi(page, (method, code) => (method === 'PUT' && code === 'SLL1017S' ? 'refused' : 'saved'))
  await openOn(page, 'Languages')
  await heart(page, 'French 1A').click()
  await expect(toast(page)).toBeVisible()
  await expect(heart(page, 'French 1A')).toHaveAttribute('aria-pressed', 'false')
  // Both writes went out together, and the one that saved was undone
  expect(asked.writes.toSorted()).toEqual(['DELETE SLL1017F', 'PUT SLL1017F', 'PUT SLL1017S'])
})

test('when the undo fails too, the electives are read again and the card shows what saved', async ({ page }) => {
  // SLL1017F saves, SLL1017S is refused, and so is the undo of SLL1017F, which stays hearted
  const asked = await madeUpApi(page, (method, code) => (code === 'SLL1017S' || method === 'DELETE' ? 'refused' : 'saved'))
  await openOn(page, 'Languages')
  await heart(page, 'French 1A').click()
  await expect(toast(page)).toBeVisible()
  await expect.poll(() => asked.reads).toBe(2)
  await expect(heart(page, 'French 1A')).toHaveAttribute('aria-pressed', 'true')
})

test("a card with no note has no line at its foot, and one she can't heart shows its note and no heart", async ({ page }) => {
  await madeUpApi(page)
  await openOn(page, 'Languages')
  const frenchCard = page.getByRole('article').filter({ has: page.getByRole('heading', { name: 'French 1A' }) })
  const greekCard = page.getByRole('article').filter({ has: page.getByRole('heading', { name: 'Greek IA' }) })
  await expect(frenchCard.getByText("Doesn't fit")).toHaveCount(0)
  await expect(frenchCard.locator('p').last()).toHaveText('Convener: Dr Made Up')
  await expect(greekCard.getByText("Doesn't fit your plans' timetables.")).toBeVisible()
  await expect(heart(page, 'Greek IA')).toHaveCount(0)
})

test('the page passes axe and the keyboard walk, on a tab with a note and a heart', async ({ page }) => {
  await madeUpApi(page)
  await openOn(page, 'Business & Management')
  await expectNoAxeViolations(page)
  const stops = await walkKeyboard(page)
  expect(stops).toContain('tab "Business & Management" [selected]')
  expect(stops).toContain('button "Favourite Marketing I"')
})
