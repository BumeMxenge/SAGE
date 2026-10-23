// The questionnaire, on made-up answers from the API, as answering is one-way and every worktree shares
// the local database, so no check saves a real student's answers. Mbali's session signs the requests
// the checks leave alone, such as GET /v1/me. Her made-up set of ten plans needs narrowing until the
// answers are saved: /plan asks one question at a time, Back keeps an answer and changing it clears a
// later one that no longer fits, a greyed answer takes focus, says why and can't be chosen, and Show My
// Plans saves the answers by id and opens the first plan they kept. Then axe, the keyboard walk and
// parity beside the planner prototype's questionnaire, in both themes.
// The questions are the prototype's own, with its plans and the plans each answer keeps, as the API
// would send them: the API's labels for the week, and no direction question (approved difference 11).
import { expect, type Page, type Route, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../../e2e/axe.ts'
import { walkKeyboard } from '../../../e2e/keyboard.ts'
import { type ParityCase, parity, type Theme } from '../../../e2e/parity.ts'
import { settled } from '../../../e2e/settled.ts'
import { mbali } from '../../../e2e/visitors.ts'
import type { components } from '../../lib/api-types.ts'

test.use({ storageState: mbali })

type PlanSet = components['schemas']['PlanSet']
type Plan = components['schemas']['Plan']
type Questionnaire = components['schemas']['Questionnaire']
type Option = components['schemas']['Option']

// The prototype's ten plans, V01 to V10, as made-up ids
const plan = (number: number) => `00000000-0000-4000-8000-0000000009${String(number).padStart(2, '0')}`
const every = Array.from({ length: 10 }, (_, index) => index + 1)
const keeping = (...numbers: number[]) => numbers.map(plan)

function setOf(kept: number[] | null): PlanSet {
  return {
    period: 2026,
    version: 1,
    questionnaire_needed: kept === null,
    reasons: [],
    plans: every.map((number) => ({
      id: plan(number),
      position: number,
      name: `Made-up Plan ${number}`,
      combination: null,
      hidden: kept !== null && !kept.includes(number),
      credits: 144,
    })),
  }
}

function planOf(number: number, kept: number[]): Plan {
  const { id, position, name, combination, hidden } = setOf(kept).plans[number - 1]
  return { id, period: 2026, position, name, combination, hidden, credits: { total: 144, by_term: {} }, courses: [], reasons: [] }
}

const option = (id: string, label: string, keeps: string[], hearted = false): Option => ({ id, label, hearted, keeps })

// The prototype's course question, with made-up codes for its courses
const courses = [
  option('TST4101F', 'Energy Conversion II', keeping(1, 2, 3, 4, 5, 6, 7)),
  option('TST4102F', 'Process Control & Instrumentation', keeping(1, 2, 3, 4, 8, 9, 10)),
  option('TST4103F', 'Mechatronics', keeping(1, 5, 6, 7, 8, 9, 10)),
  option('TST4104F', 'Digital Signal Processing', keeping(2, 5, 8)),
  option('TST4105F', 'High Performance Digital Embedded Systems', keeping(3, 6, 9)),
  option('TST4106F', 'Medical Imaging & Image Processing', keeping(4, 7, 10)),
]

function questionnaireOf(courseOptions: Option[]): Questionnaire {
  return {
    needed: true,
    questions: [
      {
        id: 'course',
        prompt: 'Is there a course you already know you want?',
        hint: 'Only plans that include it stay in.',
        options: [...courseOptions, option('no_preference', 'No strong preference', keeping(...every))],
      },
      {
        id: 'week',
        prompt: 'How should the week feel?',
        hint: null,
        options: [
          option('fewest_8am', 'Fewest 8am starts', keeping(8, 9, 10)),
          option('lunch_free', 'Keep the 13:00 lunch hour free', keeping(1, 2, 3, 5, 6, 8, 9)),
          option('no_preference', 'No preference', keeping(...every)),
        ],
      },
    ],
  }
}

// Mechatronics and Fewest 8am starts keep plans 8 to 10, the first of which /plan then opens
const kept = [8, 9, 10]

// The API is on another port, so each answer allows this page's origin, as the backend's CORS does
const allowed = { 'Access-Control-Allow-Origin': '*' }

// The made-up API: her set needs narrowing until the answers are saved, and then her answers have
// kept plans 8 to 10. A refusal, when given, answers the save instead, though the set is answered all
// the same, as when she answered in another tab. It returns what the save sent.
async function madeUpApi(page: Page, questionnaire = questionnaireOf(courses), refusal?: components['schemas']['Problem']) {
  let sent: unknown
  await page.route('**/v1/plans', (route) => route.fulfill({ json: setOf(sent === undefined ? null : kept), headers: allowed }))
  await page.route('**/v1/plans/*', (route) => {
    const number = every.find((each) => route.request().url().endsWith(plan(each)))
    return route.fulfill({ json: number && planOf(number, kept), headers: allowed })
  })
  await page.route('**/v1/questionnaire', (route: Route) => {
    if (route.request().method() === 'GET') return route.fulfill({ json: questionnaire, headers: allowed })
    sent = route.request().postDataJSON()
    if (refusal) return route.fulfill({ status: refusal.status, contentType: 'application/problem+json', json: refusal, headers: allowed })
    return route.fulfill({ json: setOf(kept), headers: allowed })
  })
  return () => sent
}

const heading = (page: Page) => page.getByRole('heading', { level: 1, name: 'A Few Questions First' })
const answer = (page: Page, name: string) => page.getByRole('radio', { name, exact: true })
const button = (page: Page, name: string) => page.getByRole('button', { name, exact: true })
const narrowing = (page: Page) => page.locator('output')

test('/plan asks one question at a time, and Show My Plans saves the answers and opens the first plan they kept', async ({ page }) => {
  const sent = await madeUpApi(page)
  // From Course History, so Back from the plan shows where she came from
  await page.goto('/history')
  await page.getByRole('heading', { level: 1, name: 'Course History' }).waitFor()
  await page.getByRole('link', { name: 'Plan', exact: true }).click()
  await expect(heading(page)).toBeVisible()
  await expect(page).toHaveURL(/\/plan$/)
  await expect(page.getByRole('radiogroup')).toHaveAccessibleName('Is there a course you already know you want?')
  await expect(narrowing(page)).toHaveText('Answer to narrow your 10 plans, or carry on to keep them all.')
  await expect(button(page, 'Back')).toHaveCount(0)

  await answer(page, 'Mechatronics').click()
  await expect(narrowing(page)).toHaveText('This keeps 7 of your 10 plans.')
  await button(page, 'Next').click()
  await expect(page.getByRole('radiogroup')).toHaveAccessibleName('How should the week feel?')
  await answer(page, 'Fewest 8am starts').click()
  await expect(narrowing(page)).toHaveText('This keeps 3 of your 10 plans.')
  await button(page, 'Show My Plans').click()

  await page.waitForURL(`**/plan/${plan(8)}`)
  expect(sent()).toEqual({ course: 'TST4103F', week: 'fewest_8am' })
  // /plan's address was replaced, so Back skips the questionnaire
  await page.goBack()
  await expect(page).toHaveURL(/\/history$/)
})

test('Back keeps the earlier answer, and changing it clears a later answer that no longer fits', async ({ page }) => {
  await madeUpApi(page)
  await page.goto('/plan')
  await answer(page, 'Mechatronics').click()
  await button(page, 'Next').click()
  await answer(page, 'Fewest 8am starts').click()
  await button(page, 'Back').click()
  await expect(answer(page, 'Mechatronics')).toBeChecked()
  // Energy Conversion II keeps plans 1 to 7, and Fewest 8am starts 8 to 10
  await answer(page, 'Energy Conversion II').click()
  await button(page, 'Next').click()
  await expect(page.getByRole('radio', { checked: true })).toHaveCount(0)
  await expect(answer(page, 'Fewest 8am starts')).toHaveAttribute('aria-disabled', 'true')
})

test('a greyed answer takes focus, says why, and neither Space nor a click chooses it', async ({ page }) => {
  await madeUpApi(page)
  await page.goto('/plan')
  await answer(page, 'Energy Conversion II').click()
  await page.keyboard.press('Tab')
  await page.keyboard.press('Enter')
  // Next moves focus to the week, onto its first answer that can be chosen
  const lunch = answer(page, 'Keep the 13:00 lunch hour free')
  await expect(lunch).toBeFocused()
  const reason = 'No plan has both ‘Energy Conversion II’ and ‘Fewest 8am starts’.'
  await expect(page.getByText(reason)).toBeVisible()

  await page.keyboard.press('ArrowLeft')
  const fewest = answer(page, 'Fewest 8am starts')
  await expect(fewest).toBeFocused()
  await expect(fewest).toHaveAttribute('aria-disabled', 'true')
  await expect(fewest).toHaveAccessibleDescription(reason)
  await expectNoAxeViolations(page)
  // Checked after each press, as a second press would clear what a first one chose
  await page.keyboard.press('Space')
  await expect(fewest).not.toBeChecked()
  // Playwright won't click an aria-disabled control unless forced, though a mouse can
  await fewest.click({ force: true })
  await expect(fewest).not.toBeChecked()
  await expect(narrowing(page)).toHaveText('This keeps 7 of your 10 plans.')
})

test('a save refused as already answered moves on to her plans', async ({ page }) => {
  await madeUpApi(page, questionnaireOf(courses), {
    type: 'about:blank',
    title: 'Conflict',
    status: 409,
    detail: 'A made-up refusal.',
    code: 'questionnaire_answered',
  })
  await page.goto('/plan')
  await button(page, 'Next').click()
  await button(page, 'Show My Plans').click()
  await page.waitForURL(`**/plan/${plan(8)}`)
})

test('each question passes axe and the keyboard walk', async ({ page }) => {
  await madeUpApi(page)
  await page.goto('/plan')
  await heading(page).waitFor()
  await expectNoAxeViolations(page)
  await walkKeyboard(page)
  await answer(page, 'Medical Imaging & Image Processing').click()
  await button(page, 'Next').click()
  // Medical Imaging keeps plans 4, 7 and 10, and the free lunch hour none of them
  await expect(answer(page, 'Keep the 13:00 lunch hour free')).toHaveAttribute('aria-disabled', 'true')
  await expectNoAxeViolations(page)
  await walkKeyboard(page)
})

// Parity. The prototype opens at the empty plan and reads its theme from its address. Create
// Registration Plan opens its questions, whose column is two divs up from its title.
async function prototypeQuestions(page: Page, theme: Theme): Promise<void> {
  if (theme === 'dark') await page.goto(`${page.url()}?theme=dark`)
  await page.getByRole('button', { name: 'Create registration plan' }).click()
  await settled(page)
}

const designedColumn = (page: Page) => page.getByRole('heading', { name: 'A few questions first' }).locator('xpath=ancestor::div[2]')
const main = (page: Page) => page.getByRole('main')

type Step = (page: Page) => Promise<void>

function state(
  name: string,
  steps: { designed: Step; built: Step },
  designed: (page: Page) => ReturnType<Page['getByRole']>,
  built: (page: Page) => ReturnType<Page['getByRole']>,
  hover = false,
): ParityCase {
  return {
    name,
    prototype: 'registration-planner',
    reach: async (page, theme) => {
      await prototypeQuestions(page, theme)
      await steps.designed(page)
      await settled(page)
      return designed(page)
    },
    react: {
      path: '/plan',
      reach: async (page) => {
        await heading(page).waitFor()
        await steps.built(page)
        await settled(page)
      },
      element: built,
    },
    hover,
  }
}

const nothing = { designed: async () => undefined, built: async () => undefined }
const chooseMechatronics = {
  designed: (page: Page) => page.getByRole('button', { name: 'Mechatronics', exact: true }).click(),
  built: (page: Page) => answer(page, 'Mechatronics').click(),
}
// Energy Conversion II leaves no plan with the fewest 8am starts. The prototype shows its reason when
// that answer is hovered; React writes it under the week's answers.
const weekAfterEnergy = {
  designed: async (page: Page) => {
    await page.getByRole('button', { name: 'Energy Conversion II', exact: true }).click()
    await page.getByRole('button', { name: 'Minimise 8am starts' }).hover()
  },
  built: async (page: Page) => {
    await answer(page, 'Energy Conversion II').click()
    await button(page, 'Next').click()
  },
}
const toWeek = {
  designed: async () => undefined,
  built: (page: Page) => button(page, 'Next').click(),
}

test.describe('parity', () => {
  test.beforeEach(async ({ page }) => {
    await madeUpApi(page)
  })

  parity('questionnaire', [
    state('questionnaire', nothing, designedColumn, main),
    state('course-chosen', chooseMechatronics, designedColumn, main),
    state('week-greyed', weekAfterEnergy, designedColumn, main),
    state(
      'answer',
      nothing,
      (page) => page.getByRole('button', { name: 'Digital Signal Processing', exact: true }),
      (page) => answer(page, 'Digital Signal Processing'),
      true,
    ),
    state('next', nothing, (page) => page.getByRole('button', { name: 'Generate plans' }), (page) => button(page, 'Next'), true),
    state(
      'show-my-plans',
      toWeek,
      (page) => page.getByRole('button', { name: 'Generate plans' }),
      (page) => button(page, 'Show My Plans'),
      true,
    ),
    state('back', toWeek, (page) => page.getByRole('button', { name: 'Back', exact: true }), (page) => button(page, 'Back'), true),
  ])
})

// Two hearted courses, which the API lists first. The prototype's questionnaire shows no hearts, so the
// image shows React alone.
test.describe('hearts', () => {
  test.beforeEach(async ({ page }) => {
    const hearted = [courses[3], courses[2]].map((course) => ({ ...course, hearted: true }))
    await madeUpApi(page, questionnaireOf([...hearted, ...courses.filter((course) => !hearted.some(({ id }) => id === course.id))]))
  })

  parity('questionnaire', [
    {
      name: 'hearts',
      prototype: 'registration-planner',
      reach: async () => null,
      react: { path: '/plan', reach: (page) => heading(page).waitFor(), element: main },
    },
  ])
})
