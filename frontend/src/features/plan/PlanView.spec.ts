// The plan view as Mbali: /plan opens her first plan, the switcher puts the plans her answers hid
// last, choosing a plan or a term changes the address, Compare pairs the next plan her answers kept,
// marks what only one plan has and returns on Done Comparing, Escape or Back, and axe and the keyboard
// walk pass on compare and the open switcher. routes.spec.ts runs both on the plan itself. Then one
// engine-shaped plan on a made-up answer from the API, and parity beside the planner prototype in
// both themes. Her plans are her seed's (data/synthetic/mbali.json): ten, of which her saved answers
// hid Signals & Power, Embedded & Power and Imaging & Control.
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
const switcher = (page: Page) => page.getByRole('button', { name: /^Power & Robotics/ })
const compareButton = (page: Page) => page.getByRole('button', { name: 'Compare', exact: true })
const day = (page: Page, name: string) => page.getByRole('list', { name })

async function openPlan(page: Page): Promise<void> {
  await page.goto('/plan')
  await page.waitForURL(planAddress)
  await switcher(page).waitFor()
}

test('/plan opens her first plan, and the switcher lists the plans her answers hid last', async ({ page }) => {
  await openPlan(page)
  await switcher(page).click()
  const options = await page.getByRole('option').allTextContents()
  const hidden = await page.getByRole('group', { name: 'Hidden by Your Answers' }).getByRole('option').allTextContents()
  const named = (texts: string[]) => texts.map((text) => text.replace(/\d+ credits$/, ''))
  expect([...named(hidden)].sort()).toEqual(['Embedded & Power', 'Imaging & Control', 'Signals & Power'])
  expect(named(options).slice(-hidden.length)).toEqual(named(hidden))
  expect(named(options)[0]).toBe('Power & Robotics')
})

test('choosing a plan opens it at its own address, and Back returns', async ({ page }) => {
  await openPlan(page)
  const first = page.url()
  await switcher(page).click()
  await page.getByRole('option', { name: /^Signals & Robotics/ }).click()
  await expect(page).not.toHaveURL(first)
  // EEE4114F is Signals & Robotics' and not Power & Robotics'
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
  // Signals & Power, Embedded & Power and Imaging & Control come between them, hidden
  for (const leave of ['Done Comparing', 'Escape', 'Back'] as const) {
    await compareButton(page).click()
    await expect(page.getByRole('heading', { level: 1, name: 'Comparing Plans' })).toBeVisible()
    await expect(panels).toHaveText(['Power & Robotics', 'Signals & Robotics'])
    if (leave === 'Done Comparing') await page.getByRole('button', { name: 'Done Comparing' }).click()
    else if (leave === 'Escape') await page.keyboard.press('Escape')
    else await page.goBack()
    await expect(page).toHaveURL(alone)
    await expect(compareButton(page)).toBeVisible()
  }
})

test('compare marks each course only one plan has, in the week and the list', async ({ page }) => {
  await openPlan(page)
  await compareButton(page).click()
  const [first, second] = [page.getByRole('article').first(), page.getByRole('article').last()]
  // Power & Robotics takes EEE4118F and Signals & Robotics EEE4114F; both take EEE4117F
  await expect(first.getByRole('list', { name: 'Tuesday' }).getByRole('listitem').filter({ hasText: 'EEE4118F' })).toContainText('only in this plan')
  await expect(second.getByRole('list', { name: 'Tuesday' }).getByRole('listitem').filter({ hasText: 'EEE4114F' })).toContainText('only in this plan')
  await expect(first.getByRole('list', { name: 'Monday' }).getByRole('listitem').filter({ hasText: 'EEE4117F' })).not.toContainText('only in this plan')
  await page.getByRole('radio', { name: 'Course List' }).click()
  await expect(first.getByRole('row', { name: /EEE4118F/ })).toContainText('Only in this plan')
  await expect(second.getByRole('row', { name: /EEE4114F/ })).toContainText('Only in this plan')
  await expect(first.getByRole('row', { name: /EEE4117F/ })).not.toContainText('Only in this plan')
})

test('compare and the open switcher pass axe, and the keyboard walks compare', async ({ page }) => {
  await openPlan(page)
  await switcher(page).click()
  await settled(page)
  await expectNoAxeViolations(page)
  await page.keyboard.press('Escape')
  await compareButton(page).click()
  await page.getByRole('heading', { level: 2 }).first().waitFor()
  await expectNoAxeViolations(page)
  await walkKeyboard(page)
})

// One plan as the engine makes them for a third-year student, on a made-up answer from the API: named
// by its electives, alone in its set, with EEE3096S's two labs, CSC3002F's practicals on the pairs of
// days that fit, and CSC3024S's practical by arrangement. Every meeting is as the 2026 rulebook or the
// engine has it. No real plan holds both CSC3024S and EEE3096S, as their lectures meet at 10:00 on
// Tuesday and Wednesday, so here they share those mornings side by side.
type PlanSet = components['schemas']['PlanSet']
type Plan = components['schemas']['Plan']
type Meeting = components['schemas']['Meeting']

const engineId = '00000000-0000-4000-8000-000000000999'
const engineName = 'CSC3002F & CSC3024S'

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
const pairs = [
  ['Monday and Wednesday', 1, 3],
  ['Monday and Thursday', 1, 4],
  ['Monday and Friday', 1, 5],
  ['Wednesday and Friday', 3, 5],
] as const
const enginePlan: Plan = {
  id: engineId,
  period: 2026,
  position: 1,
  name: engineName,
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
  plans: [{ id: engineId, position: 1, name: engineName, hidden: false, credits: 70 }],
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
  await expect(page.getByRole('button', { name: new RegExp(engineName) })).toHaveCount(0)
  await expect(compareButton(page)).toHaveCount(0)
  // Monday holds a lecture and one block for the three pairs of days that include it
  await expect(day(page, 'Monday').getByRole('listitem')).toHaveCount(2)
  await expectNoAxeViolations(page)
  mkdirSync(images, { recursive: true })
  await page.screenshot({ path: join(images, `engine-sem1-${testInfo.project.name}.png`), fullPage: true })
  await page.getByRole('radio', { name: 'Sem 2' }).click()
  await expect(page.getByText('No set times this term: CSC3024S practical: by arrangement.')).toBeVisible()
  await expectNoAxeViolations(page)
  await page.screenshot({ path: join(images, `engine-sem2-${testInfo.project.name}.png`), fullPage: true })
})

// Parity. The prototype opens at the empty plan and reads its theme from its address. Create
// Registration Plan, then Mechatronics, the course Mbali's saved answers chose, then Generate Plans opens
// Power & Robotics among the same seven plans her answers kept. Its plan area is three divs up from its
// Compare button, its plan list holds its rows, and its compare view is three divs up from its title.
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

const steps = {
  plan: { designed: async () => undefined, built: async (page: Page) => settled(page) },
  sem2: {
    designed: async (page: Page) => page.getByRole('button', { name: 'Sem 2' }).click(),
    built: async (page: Page) => page.getByRole('radio', { name: 'Sem 2' }).click(),
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
}

function state(name: string, step: { designed: Step; built: Step }, designed: (page: Page) => Locator, built: (page: Page) => Locator, hover = false): ParityCase {
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

parity('plan', [
  state('plan', steps.plan, designedPlan, main),
  state('sem2', steps.sem2, designedPlan, main),
  state('list', steps.list, designedPlan, main),
  state('switcher-list', steps.switcher, designedList, (page) => page.getByRole('listbox').locator('..')),
  state('compare', steps.compare, designedCompare, main),
  state('switcher', steps.plan, designedSwitcher, switcher, true),
  state('compare-button', steps.plan, (page) => page.getByRole('button', { name: 'Compare', exact: true }), compareButton, true),
  state(
    'plan-option',
    steps.switcher,
    (page) => page.getByRole('button', { name: /^Signals & Robotics/ }),
    (page) => page.getByRole('option', { name: /^Signals & Robotics/ }),
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
])
