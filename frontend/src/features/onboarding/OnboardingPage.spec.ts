// Parity, axe and the keyboard walk for onboarding's steps, as a student who hasn't finished setup:
// Mbali's session with a made-up answer from GET /v1/me, so no check resets a real account. The
// transcript's reading is answered here with a made-up transcript, as her session can't read
// Ilvane's PDF. Onboarding has no dark design, so dark images show React alone.
import { expect, type Locator, type Page, test } from '@playwright/test'
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

test.beforeEach(async ({ page }) => {
  await visitAs(page, 'unfinished')
  await page.route('**/v1/onboarding/transcript', (route) => route.fulfill({ json: transcript, headers: allowed }))
})

// From Account Created to the upload
async function toUpload(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Next, Your Course History' }).click()
  await page.getByRole('heading', { level: 1, name: 'Upload Your Transcript' }).waitFor()
}

// On to a transcript that has been read
async function toReady(page: Page): Promise<void> {
  await toUpload(page)
  await page
    .locator('input[type=file]')
    .setInputFiles({ name: 'transcript.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 made up') })
  await page.getByText('courses found').waitFor()
}

const whole = (page: Page) => page.locator('body')

// A whole state of onboarding, reached through the prototype's switcher and React's own controls
function state(name: string, prototypeState: string, reach: (page: Page) => Promise<void>): ParityCase {
  return {
    name,
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null
      await showState(page, prototypeState)
      await settled(page)
      return whole(page)
    },
    react: {
      path: '/onboarding',
      reach: async (page) => {
        await reach(page)
        await settled(page)
      },
      element: whole,
    },
  }
}

// One control, at rest and on hover, after React's clicks to reach it. The prototype's is null where it
// draws none.
function control(
  name: string,
  prototypeState: string,
  designed: ((page: Page) => Locator) | null,
  built: (page: Page) => Locator,
  reach?: (page: Page) => Promise<void>,
): ParityCase {
  return {
    name,
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark' || !designed) return null
      await showState(page, prototypeState)
      return designed(page)
    },
    react: { path: '/onboarding', reach, element: built },
    hover: true,
  }
}

parity('onboarding', [
  state('account-created', 'Account created', async (page) => {
    // The confetti falls once, then the page is still
    await page.getByRole('heading', { level: 1 }).waitFor()
  }),
  control(
    'next-button',
    'Account created',
    (page) => page.getByRole('button', { name: 'Next, your course history' }),
    (page) => page.getByRole('button', { name: 'Next, Your Course History' }),
  ),
  state('upload', 'Upload', toUpload),
  control(
    'drop-zone',
    'Upload',
    (page) => page.locator('[data-dc-tpl="227"]'),
    (page) => page.locator('div[data-rac]').filter({ has: page.getByRole('button', { name: 'Choose PDF' }) }),
    toUpload,
  ),
  control('choose-pdf', 'Upload', null, (page) => page.getByRole('button', { name: 'Choose PDF' }), toUpload),
  state('ready', 'Ready', toReady),
  control(
    'remove-file',
    'Ready',
    (page) => page.getByRole('button', { name: 'Remove file' }),
    (page) => page.getByRole('button', { name: 'Remove File' }),
    toReady,
  ),
  control(
    'continue',
    'Ready',
    (page) => page.getByRole('button', { name: 'Continue' }),
    (page) => page.getByRole('button', { name: 'Continue' }),
    toReady,
  ),
])

test('the upload has no axe violations and a clean keyboard walk', async ({ page }) => {
  await page.goto('/onboarding')
  await toUpload(page)
  await expectNoAxeViolations(page)
  await walkKeyboard(page)
})

test('a read transcript has no axe violations and a clean keyboard walk', async ({ page }) => {
  await page.goto('/onboarding')
  await toReady(page)
  await expect(page.getByRole('button', { name: 'Continue' })).toBeEnabled()
  await expectNoAxeViolations(page)
  await walkKeyboard(page)
})
