// Explore Electives as a made-up student with a complementary slot, on made-up answers from the API.
// Every /v1 request is answered here, and a catch-all refuses any other and fails the check, so no
// heart reaches the database every worktree shares. Mbali's session signs the browser in.
//
// It checks that hearting a course offered twice sends one PUT for each offering she can heart and
// none for one she can't; that when one of two writes fails, the other is undone, the heart comes
// back and a toast says so; that when the undo fails too, the electives are read again and the card
// shows what saved; that a card with no note has no line at its foot, and one she can't heart shows
// its note and no heart. Then the page filtered to one plan: only the courses that fit it, her
// favourites first on the tab with one, which opens first, and a reload keeps the filter; a plan
// that isn't hers, and one from an earlier set, show every course and say why; and a current plan
// nothing fits shows its slot's own words. Each passes axe, and the keyboard walks the page.
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
type Plan = components['schemas']['Plan']
type PlanSet = components['schemas']['PlanSet']
type Problem = components['schemas']['Problem']

// The API is on another port, so each answer allows this page's origin, as the backend's CORS does
const allowed = { 'Access-Control-Allow-Origin': '*' }

// Ziyela, made up, whose plans have a complementary slot
const ziyela: Me = { email: 'ntwziy999@myuct.ac.za', account: 'student', student_number: 'NTWZIY999', onboarding_complete: true }

// Made-up ids for her three current plans, and for one from an earlier set and one that isn't hers
const plan = (number: number) => `00000000-0000-4000-8000-0000000009${String(number).padStart(2, '0')}`
const earlier = plan(41)
const notHers = plan(42)

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
// whose two offerings she can, one she can't heart at all, with the API's note, one that fits her
// plan 1 alone and one that fits plan 2 alone. Nothing fits her plan 3.
const marketing = card('Marketing I', [offering('BUS2010F'), offering('BUS2010S', { can_heart: false, plans: [] })], {
  note: 'Only the semester 1 offering fits your plans.',
})
const french = card('French 1A', [offering('SLL1017F'), offering('SLL1017S')])
const greek = card('Greek IA', [offering('SLL1052F', { can_heart: false, plans: [] })], {
  note: "Doesn't fit your plans' timetables.",
})
const xhosa = card('isiXhosa for Beginners', [offering('SLL1060F', { plans: [plan(1)] })])
const ethics = card('Ethics', [offering('PHI1010S', { plans: [plan(2)] })])

const set: PlanSet = {
  period: 2026,
  version: 1,
  questionnaire_needed: false,
  has_slot: true,
  reasons: [],
  plans: [1, 2, 3].map((number) => ({
    id: plan(number),
    position: number,
    name: `Made-up Plan ${number}`,
    combination: null,
    hidden: false,
    credits: 138,
    to_choose: 18,
  })),
}

// One of her plans in full, as its read answers, with its one slot
const nowhere = 'Add one approved complementary studies course, though none on the approved list fits this plan\'s timetable, so see your advisor.'
const planOf = (id: string, position: number): Plan => ({
  id,
  period: 2026,
  position,
  name: `Made-up Plan ${position}`,
  combination: null,
  hidden: false,
  credits: { total: 138, by_term: {}, to_choose: 18 },
  courses: [],
  reasons: [],
  slots: [{ kind: 'line', credits: 18, replaces: null, message: nowhere, fit_count: 0, check_count: 0 }],
})

// What the API answers a write with: saved, or refused as a server error
type Outcome = 'saved' | 'refused'

const refusalOf = (code: Problem['code'], status: number): Problem => ({
  type: 'about:blank',
  title: 'Made Up',
  status,
  detail: 'A made-up refusal.',
  code,
})

const refuse = (route: Route, problem: Problem) =>
  route.fulfill({ status: problem.status, contentType: 'application/problem+json', json: problem, headers: allowed })

type MadeUpApi = {
  // Each write's outcome, by method and code
  outcome?: (method: string, code: string) => Outcome
  // The offerings she has hearted already
  hearts?: string[]
}

// A made-up API for one check. Its hearts are the offerings saved so far. It records every write and
// every read of the electives.
async function madeUpApi(page: Page, { outcome = () => 'saved', hearts: already = [] }: MadeUpApi = {}) {
  const hearts = new Set(already)
  const asked = { writes: [] as string[], reads: 0 }
  const electives = (): Electives => {
    const heartedIn = (each: Elective): Elective => {
      const offerings = each.offerings.map((one) => ({ ...one, hearted: hearts.has(one.code) }))
      return { ...each, offerings, hearted: offerings.some((one) => one.hearted) }
    }
    return {
      tabs: [
        { key: 'business', courses: [heartedIn(marketing)] },
        { key: 'ethics', courses: [heartedIn(ethics)] },
        { key: 'languages', courses: [heartedIn(french), heartedIn(greek), heartedIn(xhosa)] },
      ],
    }
  }
  await page.route('**/v1/me', (route) => route.fulfill({ json: ziyela, headers: allowed }))
  await page.route('**/v1/plans', (route) => route.fulfill({ json: set, headers: allowed }))
  await page.route('**/v1/plans/*', (route) => {
    const id = route.request().url().split('/').at(-1) ?? ''
    if (id === notHers) return refuse(route, refusalOf('plan_not_found', 404))
    const position = id === earlier ? 1 : Number(id.slice(-2))
    return route.fulfill({ json: planOf(id, position), headers: allowed })
  })
  await page.route('**/v1/electives', (route) => {
    asked.reads += 1
    return route.fulfill({ json: electives(), headers: allowed })
  })
  await page.route('**/v1/favourites/*', (route) => {
    const method = route.request().method()
    const code = route.request().url().split('/').at(-1) ?? ''
    asked.writes.push(`${method} ${code}`)
    if (outcome(method, code) === 'refused') return refuse(route, refusalOf('internal_error', 500))
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
const cardNamed = (page: Page, name: string) => page.getByRole('article').filter({ has: page.getByRole('heading', { name }) })
const cardNames = (page: Page) => page.getByRole('tabpanel').getByRole('heading', { level: 3 })

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
  const asked = await madeUpApi(page, { outcome: (method, code) => (method === 'PUT' && code === 'SLL1017S' ? 'refused' : 'saved') })
  await openOn(page, 'Languages')
  await heart(page, 'French 1A').click()
  await expect(toast(page)).toBeVisible()
  await expect(heart(page, 'French 1A')).toHaveAttribute('aria-pressed', 'false')
  // Both writes went out together, and the one that saved was undone
  expect(asked.writes.toSorted()).toEqual(['DELETE SLL1017F', 'PUT SLL1017F', 'PUT SLL1017S'])
})

test('when the undo fails too, the electives are read again and the card shows what saved', async ({ page }) => {
  // SLL1017F saves, SLL1017S is refused, and so is the undo of SLL1017F, which stays hearted
  const asked = await madeUpApi(page, { outcome: (method, code) => (code === 'SLL1017S' || method === 'DELETE' ? 'refused' : 'saved') })
  await openOn(page, 'Languages')
  await heart(page, 'French 1A').click()
  await expect(toast(page)).toBeVisible()
  await expect.poll(() => asked.reads).toBe(2)
  await expect(heart(page, 'French 1A')).toHaveAttribute('aria-pressed', 'true')
})

test("a card with no note has no line at its foot, and one she can't heart shows its note and no heart", async ({ page }) => {
  await madeUpApi(page)
  await openOn(page, 'Languages')
  await expect(cardNamed(page, 'French 1A').locator('p').last()).toHaveText('Convener: Dr Made Up')
  await expect(cardNamed(page, 'Greek IA').getByText("Doesn't fit your plans' timetables.")).toBeVisible()
  await expect(heart(page, 'Greek IA')).toHaveCount(0)
})

test('the page passes axe and the keyboard walk, on a tab with a note and a heart', async ({ page }) => {
  await madeUpApi(page)
  // Opened from its address, not a click, so the walk starts at the top of the page
  await page.goto('/electives?tab=business')
  await heart(page, 'Marketing I').waitFor()
  await expectNoAxeViolations(page)
  const stops = await walkKeyboard(page)
  expect(stops).toContain('tab "Business & Management" [selected]')
  expect(stops).toContain('button "Favourite Marketing I"')
})

test('filtered to a plan, it keeps only what fits, her favourites first on the tab that opens, and a reload keeps it', async ({ page }) => {
  // Plan 1 takes BUS2010F, SLL1017F and SLL1060F: Marketing I, French 1A and isiXhosa, her favourite
  await madeUpApi(page, { hearts: ['SLL1060F'] })
  await page.goto(`/electives?plan=${plan(1)}`)
  const line = page.getByText('Showing the 3 courses that fit Made-up Plan 1.')
  await expect(line).toBeVisible()
  // Languages opens, as it holds her favourite, though Business & Management comes first
  await expect(page.getByRole('tab', { name: 'Languages' })).toHaveAttribute('aria-selected', 'true')
  await expect(page.getByRole('tab', { name: 'Ethics, Politics & Values' })).toHaveCount(0)
  await expect(cardNames(page)).toHaveText(['isiXhosa for Beginners', 'French 1A'])
  await expectNoAxeViolations(page)
  await page.reload()
  await expect(line).toBeVisible()
  await page.getByRole('link', { name: 'Show Every Course' }).click()
  await expect(page).toHaveURL(/\/electives\?tab=languages$/)
  await expect(cardNames(page)).toHaveText(['French 1A', 'Greek IA', 'isiXhosa for Beginners'])
})

test("a plan that isn't hers, or isn't one of her current plans, shows every course and says why", async ({ page }) => {
  await madeUpApi(page)
  await page.goto(`/electives?plan=${notHers}&tab=languages`)
  await expect(page.getByText("This Plan Doesn't Exist")).toBeVisible()
  await expect(cardNames(page)).toHaveCount(3)
  await expectNoAxeViolations(page)
  await page.goto(`/electives?plan=${earlier}&tab=languages`)
  await expect(page.getByText("This plan isn't one of your current plans, so every course is shown.")).toBeVisible()
  await expect(cardNames(page)).toHaveCount(3)
})

test("a current plan nothing fits shows its slot's own words, with a way to every course", async ({ page }) => {
  await madeUpApi(page)
  await page.goto(`/electives?plan=${plan(3)}`)
  const empty = page.getByRole('region', { name: 'No Course Fits This Plan' })
  await expect(empty).toContainText(nowhere)
  await expect(empty.getByRole('link', { name: 'Show Every Course' })).toBeVisible()
  await expectNoAxeViolations(page)
})
