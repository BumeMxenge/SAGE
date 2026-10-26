// The plan view as Mbali: /plan opens her first plan, the switcher and Compare's list leave out the
// plans her answers hid, one of which opens by its address with its name alone, choosing a plan or a
// term changes the address, Compare pairs the next plan her answers kept and returns on Done
// Comparing, Escape or Back, every view passes axe and the keyboard walks compare. While her plans are
// held on their way, loading case 01 shows, its term and view live, in the calendar and the list, as
// do compare's panels and /plan's wait for her set: each passes axe and is photographed beside the page
// it turns into. A refused read leaves no skeleton, and the plan from the cache shows none and fades
// nothing in.
// routes.spec.ts runs both on the plan itself and on a plan that doesn't exist. Then one engine-shaped
// plan, a set of 50 plans, two plans with complementary slots, alone and compared, a preview of a
// favourite in a slot from the engine's own output, with its loading, its refusal and her favourites'
// skeleton and failure, and a set with none, on made-up answers from the API, and parity beside the
// planner prototype and the error sheet in both themes.
// Her plans are her seed's (data/synthetic/mbali.json): ten, named as the engine names them, of which
// her saved answers hid "Signals, Power & Control", "Power, Control & Embedded" and "Power, Control &
// Imaging".
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { expect, type Locator, type Page, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../../e2e/axe.ts'
import { walkKeyboard } from '../../../e2e/keyboard.ts'
import {
  forgetSeen,
  hold,
  loading,
  photographArrival,
  read,
  refusal,
  seenLoading,
  skeletons,
  watchLoading,
} from '../../../e2e/loading.ts'
import { type ParityCase, parity, type Theme } from '../../../e2e/parity.ts'
import { settled } from '../../../e2e/settled.ts'
import { mbali } from '../../../e2e/visitors.ts'
import type { components } from '../../lib/api-types.ts'

test.use({ storageState: mbali })

const planAddress = /\/plan\/[\w-]+$/
const switcher = (page: Page) => page.getByRole('button', { name: /^Power, Control & Robotics/ })
const compareButton = (page: Page) => page.getByRole('button', { name: 'Compare', exact: true })
const day = (page: Page, name: string) => page.getByRole('list', { name })

async function openPlan(page: Page): Promise<void> {
  await page.goto('/plan')
  await page.waitForURL(planAddress)
  await switcher(page).waitFor()
}

// The six plans her answers kept after her first, by position
const keptAfterFirst = [
  /^Signals, Power & Robotics/,
  /^Power, Robotics & Embedded/,
  /^Power, Robotics & Imaging/,
  /^Signals, Control & Robotics/,
  /^Control, Robotics & Embedded/,
  /^Control, Robotics & Imaging/,
]

test('/plan opens her first plan, and the switcher lists each plan her answers kept over its codes', async ({ page }) => {
  await openPlan(page)
  await switcher(page).click()
  const options = page.getByRole('option')
  // Her first plan's electives are the prototype's first plan's, under its name in code order
  await expect(options.first()).toHaveText(/^Power, Control & Robotics\s*EEE4117F · EEE4118F · EEE4119F\s*\d+ credits$/)
  await expect(options).toHaveText([/^Power, Control & Robotics/, ...keptAfterFirst])
})

test("Compare's list leaves out the plans her answers hid, and one opened by its address shows its name alone", async ({ page }) => {
  const read = page.waitForResponse((response) => new URL(response.url()).pathname === '/v1/plans')
  await openPlan(page)
  const set = (await (await read).json()) as PlanSet
  await compareButton(page).click()
  await page.getByRole('button', { name: /Compare with Another Plan/ }).click()
  await expect(page.getByRole('option')).toHaveText(keptAfterFirst)
  await page.keyboard.press('Escape')

  const hidden = set.plans.find((plan) => plan.name === 'Signals, Power & Control')
  if (!hidden?.hidden) throw new Error("Mbali's seed hides Signals, Power & Control")
  await page.goto(`/plan/${hidden.id}`)
  await expect(page.getByText(hidden.name, { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: /^Signals, Power & Control/ })).toHaveCount(0)
})

test('choosing a plan opens it at its own address, and Back returns', async ({ page }) => {
  await openPlan(page)
  const first = page.url()
  await switcher(page).click()
  await page.getByRole('option', { name: /^Signals, Power & Robotics/ }).click()
  await expect(page).not.toHaveURL(first)
  // EEE4114F is Signals, Power & Robotics' and not Power, Control & Robotics'
  await expect(day(page, 'Tuesday').getByText('EEE4114F')).toBeVisible()
  await page.goBack()
  await expect(page).toHaveURL(first)
  await expect(day(page, 'Tuesday').getByText('EEE4114F')).toHaveCount(0)
})

// From Course History, the Plan link opens her first plan in place of /plan, and the terms she looks
// at replace the address, so Back from the plan returns to Course History
test('the term is part of the address, survives a reload, carries into compare, and Back skips it', async ({ page }) => {
  await page.goto('/history')
  await page.getByRole('heading', { level: 1, name: 'Course History' }).waitFor()
  await page.getByRole('link', { name: 'Plan', exact: true }).click()
  await page.waitForURL(planAddress)
  await page.getByRole('radio', { name: 'Sem 2' }).click()
  await expect(page).toHaveURL(/\?term=sem2$/)
  await page.reload()
  await expect(page.getByRole('radio', { name: 'Sem 2' })).toBeChecked()
  await compareButton(page).click()
  await expect(page).toHaveURL(/\?compare=[\w-]+&term=sem2$/)
  await page.goBack()
  await expect(page).toHaveURL(/\/plan\/[\w-]+\?term=sem2$/)
  await page.goBack()
  await expect(page).toHaveURL(/\/history$/)
})

test('Compare pairs the next plan her answers kept, and Done Comparing, Escape and Back leave it', async ({ page }) => {
  await openPlan(page)
  const alone = page.url()
  const panels = page.getByRole('heading', { level: 2 })
  // Her second, third and fourth plans come between them, hidden
  for (const leave of ['Done Comparing', 'Escape', 'Back'] as const) {
    await compareButton(page).click()
    await expect(page.getByRole('heading', { level: 1, name: 'Comparing Plans' })).toBeVisible()
    await expect(panels).toHaveText(['Power, Control & Robotics', 'Signals, Power & Robotics'])
    if (leave === 'Done Comparing') await page.getByRole('button', { name: 'Done Comparing' }).click()
    else if (leave === 'Escape') await page.keyboard.press('Escape')
    else await page.goBack()
    await expect(page).toHaveURL(alone)
    await expect(compareButton(page)).toBeVisible()
  }
})

test('every view passes axe, and the keyboard walks compare', async ({ page }) => {
  // Seven axe runs and a keyboard walk, which took up to 28 s under a full run's load
  test.setTimeout(90_000)
  const choose = (name: string) => page.getByRole('radio', { name }).click()
  await openPlan(page)
  await switcher(page).click()
  await settled(page)
  await expectNoAxeViolations(page)
  await page.keyboard.press('Escape')
  // The list, then an empty term, as she has no winter courses
  await choose('Course List')
  await expectNoAxeViolations(page)
  await choose('Winter')
  await expectNoAxeViolations(page)
  await choose('Sem 1')
  await choose('Calendar')
  await compareButton(page).click()
  await page.getByRole('heading', { level: 2 }).first().waitFor()
  await expectNoAxeViolations(page)
  await walkKeyboard(page)
  // Opened over Sem 1's week, as the page scrolls there. Over an empty term the page is shorter than
  // the window, and axe counts the out-of-sight last plan's name as on screen but its codes, below
  // the page's end, as hidden, so finds its label isn't in its name (docs/shortfalls.md).
  await page.getByRole('button', { name: /Compare with Another Plan/ }).click()
  await settled(page)
  await expectNoAxeViolations(page)
  await page.keyboard.press('Escape')
  await choose('Course List')
  await expectNoAxeViolations(page)
  await choose('Winter')
  // Each panel's empty term sits under the panel's own title
  await expect(page.getByRole('heading', { level: 3, name: 'No Courses This Term' })).toHaveCount(2)
  await expectNoAxeViolations(page)
})

// Every read of her set and her plans
const planReads = (url: URL) => url.pathname.startsWith('/v1/plans')

test('while her plans are on their way, case 01 shows with the term and view live, and the plan replaces it', async ({
  page,
}, testInfo) => {
  await openPlan(page)
  const plans = await hold(page, planReads)
  await page.reload()
  await expect(loading(page, 'Loading your plan…')).toBeAttached()
  await expect(skeletons(main(page)).first()).toBeVisible()
  await expect(page.getByRole('radio', { name: 'Sem 1' })).toBeChecked()
  await expect(page.getByRole('radio', { name: 'Calendar' })).toBeChecked()
  await expect(day(page, 'Monday')).toHaveCount(0)
  await expectNoAxeViolations(page)
  await photographArrival(page, testInfo, 'plan', () => plans.release())
  await expect(switcher(page)).toBeVisible()
  await expect(day(page, 'Monday').getByText('EEE4117F')).toBeVisible()
})

test("choosing Course List while her plans are on their way shows the list's skeleton, and her list replaces it", async ({
  page,
}, testInfo) => {
  await openPlan(page)
  const plans = await hold(page, planReads)
  await page.reload()
  await page.getByRole('radio', { name: 'Course List' }).click()
  await expect(skeletons(main(page)).first()).toBeVisible()
  // The list's skeleton, not the week's
  await expect(main(page).getByText('Mon', { exact: true })).toHaveCount(0)
  await expect(page.getByRole('table')).toHaveCount(0)
  await expectNoAxeViolations(page)
  await photographArrival(page, testInfo, 'plan-list', () => plans.release())
  await expect(page.getByRole('radio', { name: 'Course List' })).toBeChecked()
  await expect(page.getByRole('table').first()).toBeVisible()
})

test("in compare, the bar shows at once over each panel's skeleton, which the pair replaces", async ({ page }, testInfo) => {
  await openPlan(page)
  const pair = await hold(page, read('/v1/plans/compare'))
  await compareButton(page).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Comparing Plans' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Done Comparing' })).toBeVisible()
  await expect(page.getByRole('radio', { name: 'Sem 1' })).toBeChecked()
  await expect(loading(page, 'Loading your plans…')).toBeAttached()
  await expect(skeletons(main(page)).first()).toBeVisible()
  await expectNoAxeViolations(page)
  await photographArrival(page, testInfo, 'compare', () => pair.release())
  await expect(page.getByRole('heading', { level: 2 })).toHaveText(['Power, Control & Robotics', 'Signals, Power & Robotics'])
})

test("/plan shows the plan's skeleton until her set arrives, then her first plan replaces it", async ({ page }, testInfo) => {
  const set = await hold(page, read('/v1/plans'))
  await page.goto('/plan')
  await expect(loading(page, 'Loading your plan…')).toBeAttached()
  await expect(skeletons(main(page)).first()).toBeVisible()
  await expectNoAxeViolations(page)
  await photographArrival(page, testInfo, 'plan-at-plan', async () => {
    await set.release()
    await page.waitForURL(planAddress)
  })
  await expect(switcher(page)).toBeVisible()
})

test('a refused read leaves no skeleton', async ({ page }) => {
  await openPlan(page)
  const plan = await hold(page, read(new URL(page.url()).pathname.replace('/plan/', '/v1/plans/')))
  await page.reload()
  await expect(skeletons(main(page)).first()).toBeVisible()
  // A refusal isn't tried again, so the read has failed at once
  await plan.refuse(refusal('invalid_request', 422))
  await expect(skeletons(main(page))).toHaveCount(0)
  await expect(loading(page)).toHaveCount(0)
})

test('back from another page, her plan shows from the cache at once, with no skeleton and no fade', async ({ page }) => {
  await watchLoading(page)
  await openPlan(page)
  await page.getByRole('link', { name: 'Course History', exact: true }).click()
  await page.getByRole('table').first().waitFor()
  // Course History's own fade-in ends first, as its events come a frame after it starts
  await settled(page)
  await forgetSeen(page)
  await page.getByRole('link', { name: 'Plan', exact: true }).click()
  await page.waitForURL(planAddress)
  await switcher(page).waitFor()
  await settled(page)
  expect(await seenLoading(page)).toEqual({ skeletons: 0, fades: 0 })
})

// One plan made up from the engine's real cases, on a made-up answer from the API, cut down to the
// courses that carry them: EEE3096S's two labs, CSC3002F's practicals on the pairs of days that fit,
// and CSC3024S's practical by arrangement. It is named by its electives' theme words, alone in its
// set. Every meeting is as the 2026 rulebook or the engine has it, but no student's year holds these
// three: the CSC courses are electives in Electrical and Computer Engineering's final year, EEE3096S
// is a third-year course, and CSC3024S's and EEE3096S's lectures meet at 10:00 on Tuesday and
// Wednesday, so here they share those mornings side by side.
type PlanSet = components['schemas']['PlanSet']
type Plan = components['schemas']['Plan']
type Meeting = components['schemas']['Meeting']

const engineId = '00000000-0000-4000-8000-000000000999'
// engine/themes.py gives CSC3002F "Networks" and CSC3024S "C++"
const engineName = 'Networks & C++'
const engineCombination = 'CSC3002F · CSC3024S'

function meeting(term: Meeting['term'], day: number | null, from: string | null, to: string | null, more: Partial<Meeting> = {}): Meeting {
  return {
    term,
    day,
    start_time: from === null ? null : `${from}:00`,
    end_time: to === null ? null : `${to}:00`,
    kind: null,
    choice_group: null,
    choice: null,
    ...more,
  }
}

const weekdays = [1, 2, 3, 4, 5]
// Each afternoon is in more than one pair, so it draws as one block naming the pairs it's in
const pairs = [
  ['Monday and Thursday', 1, 4],
  ['Monday and Tuesday', 1, 2],
  ['Tuesday and Thursday', 2, 4],
] as const
const enginePlan: Plan = {
  id: engineId,
  period: 2026,
  position: 1,
  name: engineName,
  combination: engineCombination,
  hidden: false,
  credits: { total: 70, by_term: { sem1: 36, sem2: 34 }, to_choose: 0 },
  reasons: [],
  slots: [],
  courses: [
    {
      code: 'CSC3002F',
      name: 'Networks and Operating Systems',
      credits: 36,
      term: 'sem1',
      groups: [],
      meetings: [
        ...weekdays.map((weekday) => meeting('sem1', weekday, '09:00', '09:45')),
        ...pairs.flatMap(([choice, ...days]) =>
          days.map((weekday) => meeting('sem1', weekday, '14:00', '18:00', { kind: 'practical', choice_group: 'practical', choice })),
        ),
      ],
    },
    {
      code: 'CSC3024S',
      name: 'Introduction to C++ Programming',
      credits: 18,
      term: 'sem2',
      groups: [],
      meetings: [
        ...weekdays.map((weekday) => meeting('sem2', weekday, '10:00', '10:45', { kind: 'lecture' })),
        meeting('sem2', null, null, null, { kind: 'practical' }),
      ],
    },
    {
      code: 'EEE3096S',
      name: 'Embedded Systems II',
      credits: 16,
      term: 'sem2',
      groups: [],
      meetings: [
        meeting('sem2', 2, '10:00', '11:45'),
        meeting('sem2', 3, '10:00', '11:45'),
        meeting('sem2', 3, '14:00', '17:45', { kind: 'lab', choice_group: 'lab', choice: 'B' }),
        meeting('sem2', 5, '14:00', '17:45', { kind: 'lab', choice_group: 'lab', choice: 'A' }),
      ],
    },
  ],
}
const engineSet: PlanSet = {
  period: 2026,
  version: 1,
  questionnaire_needed: false,
  has_slot: false,
  reasons: [],
  plans: [{ id: engineId, position: 1, name: engineName, combination: engineCombination, hidden: false, credits: 70, to_choose: 0 }],
}

// The API is on another port, so each answer allows this page's origin, as the backend's CORS does
const allowed = { 'Access-Control-Allow-Origin': '*' }
const images = join(import.meta.dirname, '..', '..', '..', 'parity', 'plan')

test('an engine plan alone in its set: its name, its options and what has no set time', async ({ page }, testInfo) => {
  await page.route('**/v1/plans', (route) => route.fulfill({ json: engineSet, headers: allowed }))
  await page.route(`**/v1/plans/${engineId}`, (route) => route.fulfill({ json: enginePlan, headers: allowed }))
  await page.goto('/plan')
  await page.waitForURL(`**/plan/${engineId}`)
  // One plan: its name, with no switcher and no Compare
  await expect(page.getByText(engineName, { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: engineName })).toHaveCount(0)
  await expect(compareButton(page)).toHaveCount(0)
  // Monday holds a lecture and one block for the two pairs that include it, which its label names
  await expect(day(page, 'Monday').getByRole('listitem')).toHaveCount(2)
  await expect(day(page, 'Monday').getByText('Practical: Monday and Thursday or Monday and Tuesday')).toBeVisible()
  await expectNoAxeViolations(page)
  mkdirSync(images, { recursive: true })
  await page.screenshot({ path: join(images, `engine-sem1-${testInfo.project.name}.png`), fullPage: true })
  await page.getByRole('radio', { name: 'Sem 2' }).click()
  await expect(page.getByText('No set times this term: CSC3024S practical: by arrangement.')).toBeVisible()
  await expectNoAxeViolations(page)
  await page.screenshot({ path: join(images, `engine-sem2-${testInfo.project.name}.png`), fullPage: true })
})

// A set of 50 plans, the most the engine makes, on a made-up answer from the API, all of which her
// answers kept, as no preference does. The last has no electives, so the engine names it Core Courses
// Only, with no codes.
type PlanSummary = components['schemas']['PlanSummary']

const fifty: PlanSummary[] = Array.from({ length: 50 }, (_, index) => {
  const position = index + 1
  const id = `00000000-0000-4000-8000-${String(position).padStart(9, '0')}999`
  if (position === 50) return { id, position, name: 'Core Courses Only', combination: null, hidden: false, credits: 72, to_choose: 0 }
  return { id, position, name: `Plan ${position} of 50`, combination: `TST4${String(position).padStart(3, '0')}F`, hidden: false, credits: 72, to_choose: 0 }
})
const fiftyPlans: Plan[] = fifty.map((summary) => ({
  ...summary,
  period: 2026,
  credits: { total: 72, by_term: { sem1: 72 }, to_choose: 0 },
  courses: [],
  reasons: [],
  slots: [],
}))

test('a set of 50 plans: the list stays in the window and scrolls to the last, which has no codes line', async ({ page }) => {
  const set: PlanSet = { period: 2026, version: 1, questionnaire_needed: false, has_slot: false, reasons: [], plans: fifty }
  await page.route('**/v1/plans', (route) => route.fulfill({ json: set, headers: allowed }))
  await page.route('**/v1/plans/*', (route) =>
    route.fulfill({ json: fiftyPlans.find(({ id }) => route.request().url().endsWith(id)), headers: allowed }),
  )
  await page.goto('/plan')
  await page.waitForURL(`**/plan/${fifty[0].id}`)
  await page.getByRole('button', { name: /^Plan 1 of 50/ }).click()
  const last = page.getByRole('option', { name: /^Core Courses Only/ })
  // Out of sight until the list scrolls under the wheel, which a list taller than the window can't
  await expect(last).not.toBeInViewport()
  await page.getByRole('listbox').hover()
  await page.mouse.wheel(0, 10_000)
  await expect(last).toBeInViewport()
  await expect(last).toHaveText(/^Core Courses Only\s*72 credits$/)
  await last.click()
  await page.waitForURL(`**/plan/${fifty[49].id}`)
})

// Two made-up plans with complementary slots, on made-up answers from the API. The first has one
// 18-credit line that 47 courses fit, 35 of them needing a check, as the engine counts Ziyela's plan 2.
// The second, for a student who still owes ASL1200S, has a place for it that 12 courses fit, and a
// line nothing fits, in the engine's own words (engine/reasons.py).
type Slot = components['schemas']['Slot']

const slotIds = ['00000000-0000-4000-8000-000000000811', '00000000-0000-4000-8000-000000000812']
const nothingFits =
  "Add one approved complementary studies course, though none on the approved list fits this plan's timetable, so see your advisor."
const line = (fields: Partial<Slot>): Slot => ({
  kind: 'line',
  credits: 18,
  replaces: null,
  message: "Add one approved complementary studies course: 51 fit this plan's timetable.",
  fit_count: 47,
  check_count: 35,
  ...fields,
})
const slotPlans: Plan[] = [
  [line({})],
  [
    line({ kind: 'place', credits: 8, replaces: 'ASL1200S', fit_count: 12, check_count: 0 }),
    line({ message: nothingFits, fit_count: 0, check_count: 0 }),
  ],
].map((slots, index) => ({
  ...enginePlan,
  id: slotIds[index],
  position: index + 1,
  name: `Made-up Plan ${index + 1}`,
  credits: { total: 138, by_term: { sem1: 36, sem2: 34 }, to_choose: slots.reduce((sum, slot) => sum + slot.credits, 0) },
  slots,
}))
const slotSet: PlanSet = {
  period: 2026,
  version: 1,
  questionnaire_needed: false,
  has_slot: true,
  reasons: [],
  plans: slotPlans.map(({ id, position, name, combination, hidden, credits }) => ({
    id,
    position,
    name,
    combination,
    hidden,
    credits: credits.total,
    to_choose: credits.to_choose,
  })),
}

async function slotApi(page: Page): Promise<void> {
  await page.route(
    (url) => url.pathname.startsWith('/v1/plans') || url.pathname === '/v1/electives',
    (route) => {
      const { pathname } = new URL(route.request().url())
      const answers: Record<string, unknown> = {
        '/v1/plans': slotSet,
        '/v1/plans/compare': { first: slotPlans[0], second: slotPlans[1], shared: [], only_first: [], only_second: [] },
        '/v1/electives': { tabs: [] },
      }
      const json = answers[pathname] ?? slotPlans.find(({ id }) => pathname.endsWith(id))
      return route.fulfill({ json, headers: allowed })
    },
  )
}

// A card, found inside whatever holds it by the heading it has
const headed = (page: Page, level: number, name: string) => ({ has: page.getByRole('heading', { level, name, exact: true }) })

test("a plan's slot card says what it needs and how many courses fit, and Browse opens Explore Electives showing only those", async ({
  page,
}, testInfo) => {
  await slotApi(page)
  await page.goto(`/plan/${slotIds[0]}`)
  await expect(page.getByText('138 credits + 18 to choose', { exact: true })).toBeVisible()
  const card = page.getByRole('article').filter(headed(page, 2, 'Complementary Studies'))
  await expect(card.getByText('Add an 18-credit complementary studies course.')).toBeVisible()
  await expect(card.getByText('47 courses fit this plan, 35 of them need a check with your advisor.')).toBeVisible()
  await expectNoAxeViolations(page)
  mkdirSync(images, { recursive: true })
  await page.screenshot({ path: join(images, `slot-${testInfo.project.name}.png`), fullPage: true })
  // The switcher gives each plan's credits the same way
  await page.getByRole('button', { name: /^Made-up Plan 1/ }).click()
  await expect(page.getByRole('option')).toHaveText([/138 credits \+ 18 to choose$/, /138 credits \+ 26 to choose$/])
  await page.keyboard.press('Escape')
  await card.getByRole('link', { name: 'Browse the 47 That Fit' }).click()
  await page.waitForURL(`**/electives?plan=${slotIds[0]}`)
})

test("in compare each panel has its slots' cards, and a slot nothing fits gives the engine's words with nothing to browse", async ({
  page,
}, testInfo) => {
  await slotApi(page)
  await page.goto(`/plan/${slotIds[0]}?compare=${slotIds[1]}`)
  const second = page.getByRole('article').filter(headed(page, 2, 'Made-up Plan 2'))
  await expect(second.getByText('138 credits + 26 to choose', { exact: true })).toBeVisible()
  const place = second.getByRole('article').filter(headed(page, 3, 'In Place of ASL1200S'))
  await expect(place.getByText('An approved complementary course of at least 8 credits.')).toBeVisible()
  await expect(place.getByText('12 courses fit this plan.')).toBeVisible()
  await expect(place.getByRole('link', { name: 'Browse the 12 That Fit' })).toHaveAttribute('href', `/electives?plan=${slotIds[1]}`)
  const nothing = second.getByRole('article').filter(headed(page, 3, 'Complementary Studies'))
  await expect(nothing.getByText(nothingFits)).toBeVisible()
  await expect(nothing.getByRole('link')).toHaveCount(0)
  const first = page.getByRole('article').filter(headed(page, 2, 'Made-up Plan 1'))
  await expect(first.getByRole('link', { name: 'Browse the 47 That Fit' })).toBeVisible()
  await expectNoAxeViolations(page)
  await page.screenshot({ path: join(images, `slot-compare-${testInfo.project.name}.png`), fullPage: true })
})

// An on-track ASPECT Mechatronics student's one plan in her fourth year, and the engine's preview of
// SLL1002S Word Power in it, as the API answers them from the 2026 timetable, trimmed to the two
// courses the preview changes. Word Power keeps lecture B, Monday to Wednesday at 16:00, which overlaps
// EEE3096S's lab B, Wednesday 14:00 to 17:45, so the preview fixes the lab to A, Friday 14:00 to 17:45.
// The credits are the engine's: 96 with 18 to choose, and 111 with Word Power's 15. Her favourites are
// Word Power, which fits the plan, and a course that fits none of hers.
type PlanPreview = components['schemas']['PlanPreview']
type PlanCourse = components['schemas']['PlanCourse']
type Elective = components['schemas']['Elective']

const aspectId = '00000000-0000-4000-8000-000000000821'
const aspectLectures = [2, 3].map((weekday) => meeting('sem2', weekday, '10:00', '11:45'))
const aspectLabA = meeting('sem2', 5, '14:00', '17:45', { kind: 'lab', choice_group: 'lab', choice: 'A' })
const embedded = (meetings: Meeting[]): PlanCourse => ({
  code: 'EEE3096S',
  name: 'Embedded Systems II',
  credits: 16,
  term: 'sem2',
  groups: [{ key: 'EB811EEE05-y4-core', label: 'Fourth Year Core Courses (ME)' }],
  meetings,
})
const aspectPlan: Plan = {
  id: aspectId,
  period: 2026,
  position: 1,
  name: 'Core Courses Only',
  combination: null,
  hidden: false,
  credits: { total: 96, by_term: { sem1: 56, sem2: 40 }, to_choose: 18 },
  reasons: [],
  slots: [line({ fit_count: 35, check_count: 25 })],
  courses: [
    embedded([...aspectLectures, meeting('sem2', 3, '14:00', '17:45', { kind: 'lab', choice_group: 'lab', choice: 'B' }), aspectLabA]),
  ],
}
const wordPower: PlanPreview = {
  plan: {
    ...aspectPlan,
    credits: { total: 111, by_term: { sem1: 56, sem2: 55 }, to_choose: 0 },
    slots: [],
    courses: [
      embedded([...aspectLectures, aspectLabA]),
      {
        code: 'SLL1002S',
        name: 'Word Power',
        credits: 15,
        term: 'sem2',
        groups: [{ key: 'complementary', label: 'Approved complementary studies courses' }],
        meetings: [1, 2, 3].map((weekday) => meeting('sem2', weekday, '16:00', '16:45', { kind: 'lecture', choice_group: 'lecture', choice: 'B' })),
      },
    ],
  },
  course_code: 'SLL1002S',
  forced: [{ course_code: 'EEE3096S', choice_group: 'lab', choice: 'A' }],
}
const favourite = (name: string, code: string, plans: string[]): Elective => ({
  codes: [code],
  name,
  credits: 15,
  summary: null,
  hearted: true,
  can_heart: true,
  note: null,
  offerings: [{ code, term: 'sem2', convener: null, hearted: true, can_heart: true, plans }],
})

async function aspectApi(page: Page): Promise<void> {
  const set: PlanSet = {
    period: 2026,
    version: 1,
    questionnaire_needed: false,
    has_slot: true,
    reasons: [],
    plans: [{ id: aspectId, position: 1, name: 'Core Courses Only', combination: null, hidden: false, credits: 96, to_choose: 18 }],
  }
  const answers: Record<string, unknown> = {
    '/v1/plans': set,
    [`/v1/plans/${aspectId}`]: aspectPlan,
    [`/v1/plans/${aspectId}/previews/SLL1002S`]: wordPower,
    '/v1/electives': {
      tabs: [
        {
          key: 'literature',
          courses: [favourite('Word Power', 'SLL1002S', [aspectId]), favourite('Writing & Editing in the Media', 'FAM2000F', [])],
        },
      ],
    },
  }
  await page.route(
    (url) => url.pathname in answers,
    (route) => route.fulfill({ json: answers[new URL(route.request().url()).pathname], headers: allowed }),
  )
}

const previewing = 'Previewing Word Power in this plan. Nothing is saved.'

test("a favourite on the slot card previews it in the week, its meetings dashed and the lab it fixes named, until End Preview or Back", async ({
  page,
}, testInfo) => {
  await aspectApi(page)
  await page.goto(`/plan/${aspectId}`)
  const slot = page.getByRole('article').filter(headed(page, 2, 'Complementary Studies'))
  // Only the favourite that fits this plan
  await expect(slot.getByRole('button', { name: /^Preview/ })).toHaveText(['Preview Word Power'])
  const preview = await hold(page, read(`/v1/plans/${aspectId}/previews/SLL1002S`))
  await slot.getByRole('button', { name: 'Preview Word Power' }).click()
  // On Sem 2, Word Power's semester
  await page.waitForURL(`**/plan/${aspectId}?preview=SLL1002S&term=sem2`)
  await expect(loading(page, 'Loading the preview…')).toBeAttached()
  await expect(skeletons(main(page)).first()).toBeVisible()
  await expectNoAxeViolations(page)
  await preview.release()
  await expect(page.getByText(previewing)).toBeVisible()
  await expect(page.getByText('96 credits + 15 with Word Power', { exact: true })).toBeVisible()
  const monday = day(page, 'Monday').getByRole('listitem')
  await expect(monday).toHaveCount(1)
  await expect(monday).toHaveAttribute('data-previewed', 'true')
  await expect(monday).toContainText('SLL1002S Word Power, in this preview')
  await expect(day(page, 'Friday').getByText('Lab A, fixed by this preview')).toBeVisible()
  await expect(day(page, 'Wednesday').getByText('Lab B')).toHaveCount(0)
  // Word Power fills the plan's one slot, so its card has gone
  await expect(slot).toHaveCount(0)
  await expectNoAxeViolations(page)
  mkdirSync(images, { recursive: true })
  await page.screenshot({ path: join(images, `preview-${testInfo.project.name}.png`), fullPage: true })
  await page.getByRole('radio', { name: 'Course List' }).click()
  await expect(page.getByRole('cell', { name: 'Word Power Preview' })).toBeVisible()
  await page.getByRole('radio', { name: 'Calendar' }).click()

  // End Preview replaces the address, leaving the plan as it was
  await page.getByRole('button', { name: 'End Preview' }).click()
  await page.waitForURL(`**/plan/${aspectId}?term=sem2`)
  await expect(page.getByText('96 credits + 18 to choose', { exact: true })).toBeVisible()
  await expect(day(page, 'Wednesday').getByText('Lab B')).toBeVisible()
  // Starting one pushes the address, so Back ends it
  await slot.getByRole('button', { name: 'Preview Word Power' }).click()
  await expect(page.getByText(previewing)).toBeVisible()
  await page.goBack()
  await page.waitForURL(`**/plan/${aspectId}?term=sem2`)
  await expect(page.getByText(previewing)).toHaveCount(0)
})

test("a preview that doesn't fit says why over the plan as it is, with End Preview and nothing to try again", async ({ page }) => {
  await aspectApi(page)
  await page.route(read(`/v1/plans/${aspectId}/previews/FAM2000F`), (route) =>
    route.fulfill({ status: 422, contentType: 'application/problem+json', json: refusal('course_doesnt_fit', 422), headers: allowed }),
  )
  await page.goto(`/plan/${aspectId}?preview=FAM2000F&term=sem2`)
  const alert = page.getByRole('alert').filter({ hasText: "That Course Doesn't Fit This Plan" })
  await expect(alert).toBeVisible()
  await expect(alert.getByRole('button', { name: 'Try Again' })).toHaveCount(0)
  await expect(page.getByText('96 credits + 18 to choose', { exact: true })).toBeVisible()
  await expect(day(page, 'Wednesday').getByText('Lab B')).toBeVisible()
  await expectNoAxeViolations(page)
  await alert.getByRole('button', { name: 'End Preview' }).click()
  await page.waitForURL(`**/plan/${aspectId}?term=sem2`)
  await expect(alert).toHaveCount(0)
})

test('her favourites on the slot card wait as skeletons, and a read that fails says so with Try Again', async ({ page }) => {
  await aspectApi(page)
  const favourites = await hold(page, read('/v1/electives'))
  await page.goto(`/plan/${aspectId}`)
  const slot = page.getByRole('article').filter(headed(page, 2, 'Complementary Studies'))
  await expect(skeletons(slot)).toHaveCount(2)
  await expect(loading(page, 'Loading your favourites…')).toBeAttached()
  await favourites.refuse(refusal('internal_error', 500))
  // A failed read is tried again three times, 1, 2 and 4 s apart
  await expect(slot.getByRole('button', { name: 'Try Again' })).toBeVisible({ timeout: 15_000 })
  await expect(skeletons(slot)).toHaveCount(0)
  await expect(slot.getByRole('link', { name: 'Browse the 35 That Fit' })).toBeVisible()
  await expectNoAxeViolations(page)
})

// The error sheet draws each planner case in light, then in dark
const inSheet = (page: Page, theme: Theme, text: string) => page.getByText(text, { exact: true }).nth(theme === 'dark' ? 1 : 0)

// A set with no plan, for a student whose record shows every year done, on a made-up answer from the
// API with the engine's own reason (engine/reasons.py), beside the error sheet's case 07
const noPlans: PlanSet = {
  period: 2026,
  version: 1,
  questionnaire_needed: false,
  has_slot: false,
  reasons: [
    {
      kind: 'conflict',
      message: "Your record shows every year's core courses done, so there's no year left to plan. See your advisor.",
      course_code: null,
      source: null,
      section: null,
      page: null,
    },
  ],
  plans: [],
}

test.describe('a set with no plans', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/v1/plans', (route) => route.fulfill({ json: noPlans, headers: allowed }))
  })

  test('says why, and passes axe', async ({ page }) => {
    await page.goto('/plan')
    await expect(page.getByRole('region', { name: 'No Plans for 2026' })).toContainText(noPlans.reasons[0].message)
    await expectNoAxeViolations(page)
  })

  parity('plan', [
    {
      name: 'no-plans',
      prototype: 'error-states',
      reach: async (page, theme) => {
        await settled(page)
        return inSheet(page, theme, 'No clash-free plan for 2026').locator('..')
      },
      react: { path: '/plan', element: (page) => page.getByRole('region', { name: 'No Plans for 2026' }) },
    },
  ])
})

// Parity. The prototype opens at the empty plan and reads its theme from its address. Create
// Registration Plan, then Mechatronics, the course Mbali's saved answers chose, then Generate Plans
// opens Power & Robotics, her Power, Control & Robotics, among the same seven plans her answers
// kept. Its plan area is three divs up from its Compare button, its plan list holds its rows, and
// its compare view is three divs up from its title.
async function prototypePlan(page: Page, theme: Theme): Promise<void> {
  if (theme === 'dark') await page.goto(`${page.url()}?theme=dark`)
  await page.getByRole('button', { name: 'Create registration plan' }).click()
  await page.getByRole('button', { name: 'Mechatronics', exact: true }).click()
  await page.getByRole('button', { name: 'Generate plans' }).click()
  await settled(page)
}

const designedPlan = (page: Page) => page.getByRole('button', { name: 'Compare', exact: true }).locator('xpath=ancestor::div[3]')
const designedCompare = (page: Page) => page.getByText('Comparing plans').locator('xpath=ancestor::div[3]')
const designedSwitcher = (page: Page) => page.getByRole('button', { name: /^Power & Robotics/ }).first()
const designedList = (page: Page) => page.getByRole('button', { name: /^Signals & Robotics/ }).locator('..')

type Step = (page: Page) => Promise<void>
type Steps = { designed: Step; built: Step }

const steps = {
  plan: { designed: async () => undefined, built: async (page: Page) => settled(page) },
  sem2: {
    designed: async (page: Page) => page.getByRole('button', { name: 'Sem 2' }).click(),
    built: async (page: Page) => page.getByRole('radio', { name: 'Sem 2' }).click(),
  },
  winter: {
    designed: async (page: Page) => page.getByRole('button', { name: 'Winter' }).click(),
    built: async (page: Page) => page.getByRole('radio', { name: 'Winter' }).click(),
  },
  list: {
    designed: async (page: Page) => page.getByRole('button', { name: 'Course list' }).click(),
    built: async (page: Page) => page.getByRole('radio', { name: 'Course List' }).click(),
  },
  switcher: {
    designed: async (page: Page) => designedSwitcher(page).click(),
    built: async (page: Page) => switcher(page).click(),
  },
  compare: {
    designed: async (page: Page) => page.getByRole('button', { name: 'Compare', exact: true }).click(),
    built: async (page: Page) => {
      await compareButton(page).click()
      await page.getByRole('heading', { level: 2 }).first().waitFor()
    },
  },
  another: {
    designed: async (page: Page) => page.getByRole('button', { name: /Compare with different plan/ }).click(),
    built: async (page: Page) => page.getByRole('button', { name: /Compare with Another Plan/ }).click(),
  },
}

// Two steps in turn, such as compare and then its list
const inTurn = (first: Steps, second: Steps): Steps => ({
  designed: async (page) => {
    await first.designed(page)
    await settled(page)
    await second.designed(page)
  },
  built: async (page) => {
    await first.built(page)
    await second.built(page)
  },
})

function state(name: string, step: Steps, designed: (page: Page) => Locator, built: (page: Page) => Locator, hover = false): ParityCase {
  return {
    name,
    prototype: 'registration-planner',
    reach: async (page, theme) => {
      await prototypePlan(page, theme)
      await step.designed(page)
      await settled(page)
      return designed(page)
    },
    react: {
      path: '/plan',
      reach: async (page) => {
        await switcher(page).waitFor()
        await step.built(page)
        await settled(page)
      },
      element: built,
    },
    hover,
  }
}

const main = (page: Page) => page.getByRole('main')
const builtList = (page: Page) => page.getByRole('listbox').locator('..')
// A plan id no account has, as routes.spec.ts opens
const missingPlan = '/plan/00000000-0000-4000-8000-000000000001'

parity('plan', [
  state('plan', steps.plan, designedPlan, main),
  state('sem2', steps.sem2, designedPlan, main),
  state('winter', steps.winter, designedPlan, main),
  state('list', steps.list, designedPlan, main),
  state('switcher-list', steps.switcher, designedList, builtList),
  state('compare', steps.compare, designedCompare, main),
  state('compare-list', inTurn(steps.compare, steps.list), designedCompare, main),
  state('compare-winter', inTurn(steps.compare, steps.winter), designedCompare, main),
  state(
    'compare-with-another-list',
    inTurn(steps.compare, steps.another),
    (page) => page.getByRole('button', { name: /^Embedded & Robotics/ }).locator('..'),
    builtList,
  ),
  {
    name: 'plan-not-found',
    prototype: 'error-states',
    reach: async (page, theme) => {
      await settled(page)
      return inSheet(page, theme, "This plan doesn't exist").locator('..')
    },
    react: {
      path: missingPlan,
      // The plan's skeleton shows until the API says there's no such plan
      reach: (page) => page.getByRole('heading', { level: 1, name: "This Plan Doesn't Exist" }).waitFor(),
      element: (page) => page.getByRole('heading', { level: 1 }).locator('..'),
    },
  },
  state('switcher', steps.plan, designedSwitcher, switcher, true),
  state('compare-button', steps.plan, (page) => page.getByRole('button', { name: 'Compare', exact: true }), compareButton, true),
  state('term', steps.plan, (page) => page.getByRole('button', { name: 'Sem 2' }), (page) => page.getByRole('radio', { name: 'Sem 2' }), true),
  state('view', steps.plan, (page) => page.getByRole('button', { name: 'Course list' }), (page) => page.getByRole('radio', { name: 'Course List' }), true),
  state(
    'plan-option',
    steps.switcher,
    (page) => page.getByRole('button', { name: /^Signals & Robotics/ }),
    (page) => page.getByRole('option', { name: /^Signals, Power & Robotics/ }),
    true,
  ),
  state(
    'done-comparing',
    steps.compare,
    (page) => page.getByRole('button', { name: 'Done comparing' }),
    (page) => page.getByRole('button', { name: 'Done Comparing' }),
    true,
  ),
  state(
    'compare-with-another',
    steps.compare,
    (page) => page.getByRole('button', { name: /Compare with different plan/ }),
    (page) => page.getByRole('button', { name: /Compare with Another Plan/ }),
    true,
  ),
  {
    name: 'go-to-plan',
    prototype: 'error-states',
    reach: async (page, theme) => {
      await settled(page)
      return inSheet(page, theme, 'Go to my plan')
    },
    react: { path: missingPlan, element: (page) => page.getByRole('link', { name: 'Go to My Plan' }) },
    hover: true,
  },
])
