// Parity, axe and the keyboard walk for onboarding's steps, as a student who hasn't finished setup:
// Mbali's session with a made-up answer from GET /v1/me, so no check resets a real account. The
// transcript's reading is answered here with a made-up transcript, as her session can't read
// Ilvane's PDF. Onboarding has no dark design, so dark images show React alone.
import { type Locator, type Page, test } from '@playwright/test'
import { expectNoAxeViolations } from '../../../e2e/axe.ts'
import { walkKeyboard } from '../../../e2e/keyboard.ts'
import { type ParityCase, parity } from '../../../e2e/parity.ts'
import { mbali, visitAs } from '../../../e2e/visitors.ts'
import type { components } from '../../lib/api-types.ts'
import { settled, showState } from './prototype.ts'

type TranscriptLine = components['schemas']['TranscriptLine']

const line = (
  academic_year: number,
  term: TranscriptLine['term'],
  course_code: string,
  course_name: string,
  credits: number,
  result: string,
  mark: number | null,
  unverified = false,
): TranscriptLine => ({ academic_year, term, course_code, course_name, credits, nqf_level: academic_year - 2018, result, mark, unverified })

// A made-up record: three years, a note that some results are pending, and one line partly guessed
const transcript: components['schemas']['Transcript'] = {
  student_number: 'DLMMBA999',
  programme: 'Bachelor of Science in Engineering in Electrical and Computer Engineering',
  curriculum_options: [
    { code: 'EB022EEE02', name: 'Bachelor of Science in Engineering in Electrical and Computer Engineering 4-year curriculum' },
  ],
  issued_on: '2026-01-20',
  lines: [
    line(2023, 'sem1', 'MAM1020F', 'Mathematics 1A for Engineers', 18, '2+', 72),
    line(2023, 'sem1', 'PHY1012F', 'Physics A for Engineers', 18, '2-', 64),
    line(2023, 'sem1', 'CSC1015F', 'Computer Science 1015', 18, '1', 81),
    line(2023, 'sem1', 'EEE1006F', 'Intro Electrical Engineering', 12, '2-', 66),
    line(2023, 'sem2', 'MAM1021S', 'Mathematics 1B for Engineers', 18, '2-', 61),
    line(2023, 'sem2', 'PHY1013S', 'Physics B for Engineers', 18, '3', 55),
    line(2023, 'sem2', 'CSC1016S', 'Computer Science 1016', 18, '2+', 71),
    line(2023, 'full_year', 'EEE1000X', 'Practical Training', 0, 'GIP', null),
    line(2024, 'sem1', 'EEE2045F', 'Analogue Electronics', 16, '2-', 63),
    line(2024, 'sem1', 'EEE2046F', 'Embedded Systems I', 16, '1', 77),
    line(2024, 'sem1', 'MAM2083F', 'Vector Calculus for Engineers', 18, '3', 52),
    line(2024, 'sem1', 'MEC1009F', 'Intro to Engineering Mechanics', 16, '2-', 60),
    line(2024, 'sem2', 'EEE2044S', 'Introduction to Power Eng', 16, '2+', 70),
    line(2024, 'sem2', 'EEE2047S', 'Signals and Systems I', 16, 'SP', 50),
    line(2024, 'sem2', 'MAM2084S', 'Linear Alg & DE for Engineers', 18, '2-', 62),
    line(2024, 'sem2', 'PHY2010S', 'Electromagnetism for Engineers', 18, '3', 57),
    line(2025, 'sem1', 'EEE3088F', 'Design Principles', 16, '2+', 73),
    line(2025, 'sem1', 'EEE3090F', 'Electronic Devices & Circuits', 16, '2-', 65),
    line(2025, 'sem1', 'EEE3091F', 'Energy Conversion I', 16, '1', 79),
    line(2025, 'sem1', 'MEC2047F', 'Engineering Dynamics', 16, '3', 54, true),
    line(2025, 'sem2', 'EEE3094S', 'Control Systems Engineering', 16, 'OS', null),
    line(2025, 'sem2', 'EEE3096S', 'Embedded Systems II', 16, 'OS', null),
    line(2025, 'full_year', 'EEE3000X', 'Practical Training', 0, 'GIP', null),
  ],
  warnings: [
    {
      code: 'results_pending',
      message: "Some of your 2025 results aren't out yet, so those courses are marked in progress. Check them before you finish.",
    },
  ],
}

// The API is on another port, so each answer allows this page's origin, as the backend's CORS does
const allowed = { 'Access-Control-Allow-Origin': '*' }

test.use({ storageState: mbali })

// Her session must never write: the reading and Finish Setup are answered here, so nothing can replace
// her saved course history
test.beforeEach(async ({ page }) => {
  await visitAs(page, 'unfinished')
  await page.route('**/v1/onboarding/transcript', (route) => route.fulfill({ json: transcript, headers: allowed }))
  await page.route('**/v1/onboarding/complete', (route) =>
    route.fulfill({
      json: { email: 'dlmmba999@myuct.ac.za', account: 'student', student_number: 'DLMMBA999', onboarding_complete: true },
      headers: allowed,
    }),
  )
})

type Reach = (page: Page) => Promise<void>

// React's steps, each from the page as it opens
async function toUpload(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Next, Your Course History' }).click()
  await page.getByRole('heading', { level: 1, name: 'Upload Your Transcript' }).waitFor()
}

async function toReady(page: Page): Promise<void> {
  await toUpload(page)
  await page
    .locator('input[type=file]')
    .setInputFiles({ name: 'transcript.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 made up') })
  await page.getByText('courses found').waitFor()
}

async function toReview(page: Page): Promise<void> {
  await toReady(page)
  await page.getByRole('button', { name: 'Continue' }).click()
  await page.getByRole('heading', { level: 1, name: 'Review Your Course History' }).waitFor()
}

async function toYear2(page: Page): Promise<void> {
  await toReview(page)
  await page.getByRole('button', { name: 'Confirm 2023' }).click()
  await page.getByRole('button', { name: 'Confirm 2024' }).waitFor()
}

async function toLastYear(page: Page): Promise<void> {
  await toYear2(page)
  await page.getByRole('button', { name: 'Confirm 2024' }).click()
  await page.getByText('This reflects my current academic record').click()
}

async function toEditing(page: Page): Promise<void> {
  await toReview(page)
  await page.getByRole('button', { name: 'Edit Courses' }).click()
  await page.getByRole('button', { name: 'Done Editing' }).waitFor()
}

async function toPicker(page: Page): Promise<void> {
  await toEditing(page)
  await page.getByRole('button', { name: 'Add a Course' }).click()
  await page.getByRole('dialog', { name: 'Add a Course' }).waitFor()
}

async function toPickerWithNoMatch(page: Page): Promise<void> {
  await toPicker(page)
  await page.getByRole('searchbox').fill('zzzz')
}

async function toConfirmAdd(page: Page): Promise<void> {
  await toPicker(page)
  await page.getByRole('option').first().click()
  await page.getByRole('dialog', { name: 'Add This Course?' }).getByRole('button', { name: /Outcome for/ }).click()
  await page.getByRole('option', { name: 'Pass (pass or fail course)' }).click()
}

async function toConfirmChange(page: Page): Promise<void> {
  await toEditing(page)
  await page.getByRole('button', { name: /Outcome for/ }).first().click()
  await page.getByRole('option', { name: 'Third class (50 to 59%)' }).click()
  await page.getByRole('dialog', { name: 'Change This Outcome?' }).waitFor()
}

// A row's Remove, named after its course, such as Remove CSC1015F
const removeRow = (page: Page) => page.getByRole('button', { name: /^Remove [A-Z]{3}\d{4}[A-Z]$/ }).first()

async function toConfirmRemove(page: Page): Promise<void> {
  await toEditing(page)
  await removeRow(page).click()
  await page.getByRole('dialog', { name: 'Remove This Course?' }).waitFor()
}

// The prototype unlocks each year's Confirm only once that year's list has been scrolled to its end
async function scrollList(page: Page): Promise<void> {
  await page.mouse.move(640, 500)
  await page.mouse.wheel(0, 3000)
}

// The prototype's review, on through its years, letting each year arrive before scrolling it
async function prototypeYears(page: Page, confirms: string[]): Promise<void> {
  await showState(page, 'Review')
  for (const label of confirms) {
    await settled(page)
    await scrollList(page)
    await page.getByRole('button', { name: label }).click()
  }
  await settled(page)
}

async function prototypeLastYear(page: Page): Promise<void> {
  await prototypeYears(page, ['Confirm 2023', 'Confirm 2024'])
  await scrollList(page)
  await page.getByText('This reflects my current academic record').click()
}

// The prototype's review in edit mode, and its pickers and questions. Each year has its own controls,
// side by side in the page, so the first of each is year 1's.
async function prototypeEditing(page: Page): Promise<void> {
  await showState(page, 'Review')
  await settled(page)
  await page.getByRole('button', { name: 'Edit courses' }).first().click()
  await settled(page)
}

async function prototypePicker(page: Page): Promise<void> {
  await prototypeEditing(page)
  await page.getByRole('button', { name: 'Add a course' }).first().click()
  await settled(page)
}

async function prototypePickerWithNoMatch(page: Page): Promise<void> {
  await prototypePicker(page)
  await page.getByPlaceholder('Search by course name or code').fill('zzzz')
  await settled(page)
}

async function prototypeConfirmAdd(page: Page): Promise<void> {
  await prototypePicker(page)
  await page.getByRole('button', { name: /^EEE2044S/ }).click()
  await settled(page)
  await page.locator('select').filter({ hasText: 'Set the outcome' }).first().selectOption({ label: 'Passed' })
  await settled(page)
}

async function prototypeConfirmChange(page: Page): Promise<void> {
  await prototypeEditing(page)
  await page.locator('select').first().selectOption({ label: 'Failed' })
  await settled(page)
}

async function prototypeConfirmRemove(page: Page): Promise<void> {
  await prototypeEditing(page)
  await page.getByRole('button', { name: 'Remove course' }).first().click()
  await settled(page)
}

const whole = (page: Page) => page.locator('body')
const button = (name: string) => (page: Page) => page.getByRole('button', { name })
const show = (state: string) => (page: Page) => showState(page, state)

// A whole state, reached through the prototype's own controls and React's
function state(name: string, designed: Reach, built: Reach): ParityCase {
  return {
    name,
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null
      await designed(page)
      await settled(page)
      return whole(page)
    },
    react: {
      path: '/onboarding',
      reach: async (page) => {
        await built(page)
        await settled(page)
      },
      element: whole,
    },
  }
}

// One control, at rest and on hover, where each side's clicks leave it. The prototype's is null where
// it draws none.
function control(
  name: string,
  designed: { reach: Reach; element: (page: Page) => Locator } | null,
  built: { reach?: Reach; element: (page: Page) => Locator },
): ParityCase {
  return {
    name,
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark' || !designed) return null
      await designed.reach(page)
      return designed.element(page)
    },
    react: { path: '/onboarding', ...built },
    hover: true,
  }
}

parity('onboarding', [
  state('account-created', show('Account created'), async (page) => {
    // The confetti falls once, then the page is still
    await page.getByRole('heading', { level: 1 }).waitFor()
  }),
  control(
    'next-button',
    { reach: show('Account created'), element: button('Next, your course history') },
    { element: button('Next, Your Course History') },
  ),
  state('upload', show('Upload'), toUpload),
  control(
    'drop-zone',
    { reach: show('Upload'), element: (page) => page.locator('[data-dc-tpl="227"]') },
    { reach: toUpload, element: (page) => page.locator('div[data-rac]').filter({ has: page.getByRole('button', { name: 'Choose PDF' }) }) },
  ),
  control('choose-pdf', null, { reach: toUpload, element: button('Choose PDF') }),
  state('ready', show('Ready'), toReady),
  control('remove-file', { reach: show('Ready'), element: button('Remove file') }, { reach: toReady, element: button('Remove File') }),
  control('continue', { reach: show('Ready'), element: button('Continue') }, { reach: toReady, element: button('Continue') }),
  state('review', show('Review'), toReview),
  state('review-year-2', (page) => prototypeYears(page, ['Confirm 2023']), toYear2),
  state('review-last-year', prototypeLastYear, toLastYear),
  control(
    'back',
    // The prototype keeps every year in the page, side by side, so its first Back is year 2's
    { reach: (page) => prototypeYears(page, ['Confirm 2023']), element: (page) => page.getByRole('button', { name: 'Back' }).first() },
    { reach: toYear2, element: button('Back') },
  ),
  control(
    'confirm-year',
    {
      reach: async (page) => {
        await prototypeYears(page, ['Confirm 2023'])
        await scrollList(page)
      },
      element: button('Confirm 2024'),
    },
    { reach: toYear2, element: button('Confirm 2024') },
  ),
  control(
    'finish-setup',
    { reach: prototypeLastYear, element: button('Finish setup') },
    { reach: toLastYear, element: button('Finish Setup') },
  ),
  state('review-edit', prototypeEditing, toEditing),
  control(
    'edit-courses',
    { reach: show('Review'), element: (page) => page.getByRole('button', { name: 'Edit courses' }).first() },
    { reach: toReview, element: button('Edit Courses') },
  ),
  control('done-editing', { reach: prototypeEditing, element: button('Done editing') }, { reach: toEditing, element: button('Done Editing') }),
  control(
    'add-course',
    { reach: prototypeEditing, element: (page) => page.getByRole('button', { name: 'Add a course' }).first() },
    { reach: toEditing, element: button('Add a Course') },
  ),
  control(
    'outcome-select',
    { reach: prototypeEditing, element: (page) => page.locator('select').first() },
    { reach: toEditing, element: (page) => page.getByRole('button', { name: /Outcome for/ }).first() },
  ),
  control(
    'remove-row',
    { reach: prototypeEditing, element: (page) => page.getByRole('button', { name: 'Remove course' }).first() },
    { reach: toEditing, element: removeRow },
  ),
  state('course-picker', prototypePicker, toPicker),
  control(
    'picker-option',
    { reach: prototypePicker, element: (page) => page.getByRole('button', { name: /^EEE2044S/ }) },
    { reach: toPicker, element: (page) => page.getByRole('option').first() },
  ),
  state('picker-no-match', prototypePickerWithNoMatch, toPickerWithNoMatch),
  state('confirm-add', prototypeConfirmAdd, toConfirmAdd),
  state('confirm-change', prototypeConfirmChange, toConfirmChange),
  state('confirm-remove', prototypeConfirmRemove, toConfirmRemove),
  control(
    'remove-course-button',
    // The prototype's dialog sits last in its page, after every row's own Remove course
    { reach: prototypeConfirmRemove, element: (page) => page.getByRole('button', { name: 'Remove course' }).last() },
    { reach: toConfirmRemove, element: (page) => page.getByRole('dialog').getByRole('button', { name: 'Remove Course' }) },
  ),
])

// Each step as it stands has no axe violations and a clean keyboard walk
for (const [step, reach] of [
  ['the upload', toUpload],
  ['a read transcript', toReady],
  ["the review's first year", toReview],
  ["the review's last year, confirmed", toLastYear],
  ['editing the review', toEditing],
  ['the course picker', toPicker],
  ['the course picker with no match', toPickerWithNoMatch],
  ['adding a course', toConfirmAdd],
  ['changing an outcome', toConfirmChange],
  ['removing a course', toConfirmRemove],
] as const) {
  test(`${step} has no axe violations and a clean keyboard walk`, async ({ page }) => {
    await page.goto('/onboarding')
    await reach(page)
    await expectNoAxeViolations(page)
    await walkKeyboard(page)
  })
}
