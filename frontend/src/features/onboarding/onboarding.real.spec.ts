// The real round trip, once: Ilvane, signed in afresh, uploads the made-up transcript make transcript
// writes, confirms her course history and reaches her plans, against the real API. On the way, nothing
// from her transcript may be left in the browser's storage (POPIA). Each run resets her account, so
// it runs in the light project only, and one test at a time.
import { execFileSync } from 'node:child_process'
import { join } from 'node:path'
import { expect } from '@playwright/test'
import { test } from '../../../e2e/visitors.ts'

test.describe.configure({ mode: 'serial' })
test.skip(({ colorScheme }) => colorScheme === 'dark', 'it resets Ilvane, so the light project alone runs it')

// make transcript writes her PDF to local/transcript.pdf
function transcriptPdf(): string {
  const repo = join(import.meta.dirname, '..', '..', '..', '..')
  execFileSync('make', ['--no-print-directory', '-C', repo, 'transcript'])
  return join(repo, 'local', 'transcript.pdf')
}

test('Ilvane sets up her account from her transcript and reaches her plans', async ({ freshStudent: page }) => {
  await page.getByRole('button', { name: 'Next, Your Course History' }).click()
  await page.locator('input[type=file]').setInputFiles(transcriptPdf())
  await expect(page.getByText('courses found')).toBeVisible()
  await page.getByRole('button', { name: 'Continue' }).click()

  // The first year's courses, as the review shows them, appear nowhere in the browser's storage
  const courses = await page.locator('tbody td:first-child').allTextContents()
  const kept = await page.evaluate(async () =>
    JSON.stringify([Object.entries(localStorage), Object.entries(sessionStorage), await indexedDB.databases()]),
  )
  expect(courses.length).toBeGreaterThan(0)
  for (const course of courses) expect(kept).not.toContain(course.split(':')[0])

  // Her transcript names two Mechatronics programmes, so she chooses hers
  await page.getByRole('button', { name: /Choose your programme/ }).click()
  await page.getByRole('option', { name: 'Bachelor of Science in Engineering in Mechatronics 4-year curriculum' }).click()
  await page.getByRole('button', { name: 'Confirm 2023' }).click()
  await page.getByRole('button', { name: 'Confirm 2024' }).click()
  await page.getByText('This reflects my current academic record').click()
  await page.getByRole('button', { name: 'Finish Setup' }).click()

  await page.waitForURL('**/plan')
})
