// The plan view as Mbali: /plan opens her first plan, the switcher puts the plans her answers hid
// last, choosing a plan or a term changes the address, Compare pairs the next plan her answers kept
// and returns on Done Comparing, Escape or Back, every view passes axe and the keyboard walks compare.
// routes.spec.ts runs both on the plan itself and on a plan that doesn't exist. Then one engine-shaped
// plan, a set of 50 plans and a set with none on made-up answers from the API, and parity beside the
// planner prototype and the error sheet in both themes.
// Her plans are her seed's (data/synthetic/mbali.json): ten, named as the engine names them, of which
// her saved answers hid "Signals, Power & Control", "Power, Control & Embedded" and "Power, Control &
// Imaging".
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { expect, type Locator, type Page, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../../e2e/axe.ts'
import { walkKeyboard } from '../../../e2e/keyboard.ts'
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

test('/plan opens her first plan, and the switcher lists each over its codes, those her answers hid last', async ({ page }) => {
  await openPlan(page)
  await switcher(page).click()
  const options = page.getByRole('option')
  const hidden = page.getByRole('group', { name: 'Hidden by Your Answers' }).getByRole('option')
  // Her first plan's electives are the prototype's first plan's, under its name in code order
  await expect(options.first()).toHaveText(/^Power, Control & Robotics\s*EEE4117F · EEE4118F · EEE4119F\s*\d+ credits$/)
  await expect(hidden).toHaveText([/^Signals, Power & Control/, /^Power, Control & Embedded/, /^Power, Control & Imaging/])
  expect((await options.allTextContents()).slice(-3)).toEqual(await hidden.allTextContents())
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
  credits: { total: 70, by_term: { sem1: 36, sem2: 34 } },
  reasons: [],
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
  reasons: [],
  plans: [{ id: engineId, position: 1, name: engineName, combination: engineCombination, hidden: false, credits: 70 }],
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

// A set of 50 plans, the most the engine makes, on a made-up answer from the API, of which her answers
// kept five. The last has no electives, so the engine names it Core Courses Only, with no codes.
type PlanSummary = components['schemas']['PlanSummary']

const fifty: PlanSummary[] = Array.from({ length: 50 }, (_, index) => {
  const position = index + 1
  const id = `00000000-0000-4000-8000-${String(position).padStart(9, '0')}999`
  const hidden = position > 5
  if (position === 50) return { id, position, name: 'Core Courses Only', combination: null, hidden, credits: 72 }
  return { id, position, name: `Plan ${position} of 50`, combination: `TST4${String(position).padStart(3, '0')}F`, hidden, credits: 72 }
})
const fiftyPlans: Plan[] = fifty.map((summary) => ({
  ...summary,
  period: 2026,
  credits: { total: 72, by_term: { sem1: 72 } },
  courses: [],
  reasons: [],
}))

test('a set of 50 plans: the list stays in the window and scrolls to the last, which has no codes line', async ({ page }) => {
  const set: PlanSet = { period: 2026, version: 1, questionnaire_needed: false, reasons: [], plans: fifty }
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

// The error sheet draws each planner case in light, then in dark
const inSheet = (page: Page, theme: Theme, text: string) => page.getByText(text, { exact: true }).nth(theme === 'dark' ? 1 : 0)

// A set with no plan, for a student whose record shows every year done, on a made-up answer from the
// API with the engine's own reason (engine/reasons.py), beside the error sheet's case 07
const noPlans: PlanSet = {
  period: 2026,
  version: 1,
  questionnaire_needed: false,
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
// Registration Plan, then Mechatronics, the course Mbali's saved answers chose, then Generate Plans opens
// Power & Robotics, her Power, Control & Robotics, among the same seven plans her answers kept. Its
// plan area is three divs up from its Compare button, its plan list holds its rows, and its compare view
// is three divs up from its title.
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
    react: { path: missingPlan, element: (page) => page.getByRole('heading', { level: 1 }).locator('..') },
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
