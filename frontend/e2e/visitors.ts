// Who visits in the UI checks. Mbali signs in once per run, through make sign-in. Staff, an account
// from outside UCT and a student who hasn't finished setup are her session with a made-up answer from
// GET /v1/me, so no check resets a real account: every worktree runs these checks against the same
// local database. A spec that needs a real account to go through onboarding asks for freshStudent.
import { execFileSync } from 'node:child_process'
import { join } from 'node:path'
import { type Page, test as base } from '@playwright/test'
import type { components } from '../src/lib/api-types.ts'

// Mbali's saved sign-in, which sign-in.setup.ts writes. It holds a session token, so it stays in the
// git-ignored e2e/.auth/ and is never printed.
export const mbali = join(import.meta.dirname, '.auth', 'mbali.json')

// The one-time link a make target prints, for the frontend on PORT, which make reads from the
// environment. Only the link goes to stdout.
export function signInLink(target: 'sign-in' | 'sign-in-new'): string {
  const repo = join(import.meta.dirname, '..', '..')
  return execFileSync('make', ['--no-print-directory', '-C', repo, target], { encoding: 'utf8' }).trim()
}

type Me = components['schemas']['Me']
type Problem = components['schemas']['Problem']

const staff: Me = { email: 'test.advisor@uct.ac.za', account: 'staff', student_number: null, onboarding_complete: false }
const unfinished: Me = {
  email: 'qrtilv999@myuct.ac.za',
  account: 'student',
  student_number: 'QRTILV999',
  onboarding_complete: false,
}
const refused: Problem = {
  type: 'about:blank',
  title: 'Forbidden',
  status: 403,
  detail: 'SAGE is for UCT students and staff. Sign in with your UCT Microsoft account.',
  code: 'uct_account_required',
}

// The API is on another port, so each answer allows this page's origin, as the backend's CORS does
const allowed = { 'Access-Control-Allow-Origin': '*' }
const answers = {
  staff: { json: staff, headers: allowed },
  unfinished: { json: unfinished, headers: allowed },
  refused: { status: 403, contentType: 'application/problem+json', json: refused, headers: allowed },
}

// Makes the page's GET /v1/me answer as a made-up visitor, before the page opens
export async function visitAs(page: Page, who: keyof typeof answers): Promise<void> {
  await page.route('**/v1/me', (route) => route.fulfill(answers[who]))
}

// Ilvane's real account, signed in afresh, for a spec that goes through onboarding. Each use resets
// her with make sign-in-new, so a spec asks for it only in a file whose tests run one at a time
// (test.describe.configure({ mode: 'serial' })), and only where that reset is wanted.
export const test = base.extend<{ freshStudent: Page }>({
  freshStudent: async ({ page }, provide) => {
    await page.goto(signInLink('sign-in-new'))
    await page.waitForURL('**/onboarding')
    await provide(page)
  },
})
