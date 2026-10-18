// @vitest-environment node
// The guard sweep, like the backend's in tests/unit/api/test_guards.py: every page in the real route
// table, opened by every kind of visitor, in a memory router. Who may open each page, and where each
// visitor belongs, are written out by hand from the foundations brief, so a page that forgets its rule,
// or one added without a line here, fails. GET /v1/me is answered in place of the network, through the
// real client and its middleware. It runs in Node, because Node's Request refuses jsdom's AbortSignal.
import type { Session } from '@supabase/supabase-js'
import { createMemoryRouter, type RouteObject } from 'react-router'
import { afterEach, expect, it, vi } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { queryClient } from '@/lib/queryClient.ts'
import { refresh } from '@/lib/queryKeys.ts'
import { supabase } from '@/lib/supabase.ts'
import { routes } from './routes.tsx'

// The sign-in waiting in the address bar, finished unless a test holds it back
const held = vi.hoisted(() => ({ signIn: Promise.resolve({ error: null }) }))
vi.mock('@/lib/auth/session.ts', () => ({
  get signInFinished() {
    return held.signIn
  },
}))

// The network, replaced before the client captures it
const network = vi.hoisted(() => {
  const answer = vi.fn<typeof fetch>()
  vi.stubGlobal('fetch', answer)
  return answer
})

type Visitor = 'signed_out' | 'refused' | 'staff' | 'onboarding' | 'student'

// Who may open each page
const opens: Record<string, Visitor> = {
  '/sign-in': 'signed_out',
  '/onboarding': 'onboarding',
  '/wrong-account': 'refused',
  '/staff': 'staff',
  '/plan': 'student',
  '/plan/:planId': 'student',
  '/electives': 'student',
  '/history': 'student',
  '*': 'student',
}

// Where each visitor belongs
const home: Record<Visitor, string> = {
  signed_out: '/sign-in',
  refused: '/wrong-account',
  staff: '/staff',
  onboarding: '/onboarding',
  student: '/plan',
}

type Me = components['schemas']['Me']
type Problem = components['schemas']['Problem']

// Made-up accounts: Mbali has finished setup, and Ilvane hasn't
const mbali: Me = { email: 'dlmmba999@myuct.ac.za', account: 'student', student_number: 'DLMMBA999', onboarding_complete: true }
const ilvane: Me = { email: 'qrtilv999@myuct.ac.za', account: 'student', student_number: 'QRTILV999', onboarding_complete: false }
const staff: Me = { email: 'test.advisor@uct.ac.za', account: 'staff', student_number: null, onboarding_complete: false }

const answer = (body: Me) => new Response(JSON.stringify(body), { headers: { 'Content-Type': 'application/json' } })

function refusal(code: Problem['code'], status: number): Response {
  const body: Problem = { type: 'about:blank', title: 'Refused', status, detail: 'A made-up refusal.', code }
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/problem+json' } })
}

// Each kind of visitor, by what their browser holds and what GET /v1/me says to them
type Visit = { who: string; is: Visitor; me?: () => Response }
const visits: Visit[] = [
  { who: 'a signed-out visitor', is: 'signed_out' },
  { who: 'a visitor whose session the API refuses', is: 'signed_out', me: () => refusal('not_signed_in', 401) },
  { who: 'an account from outside UCT', is: 'refused', me: () => refusal('uct_account_required', 403) },
  { who: 'staff', is: 'staff', me: () => answer(staff) },
  { who: "a student who hasn't finished setup", is: 'onboarding', me: () => answer(ilvane) },
  { who: 'an onboarded student', is: 'student', me: () => answer(mbali) },
]

const session = { access_token: 'made-up-token' } as Session

// The visitor's browser and the API's answer to them. It returns the session's spy, to see when the
// guard first asks.
function arrive({ me }: Visit) {
  if (me) network.mockImplementation(async () => me())
  return vi
    .spyOn(supabase.auth, 'getSession')
    .mockResolvedValue(me ? { data: { session }, error: null } : { data: { session: null }, error: null })
}

// Every path in the table, through the layout routes
function paths(table: RouteObject[]): string[] {
  return table.flatMap((route) => [...(route.path ? [route.path] : []), ...paths(route.children ?? [])])
}

// An address that opens the path
const address = (path: string) =>
  ({ '/plan/:planId': '/plan/00000000-0000-4000-8000-000000000001', '*': '/no-such-page' })[path] ?? path

// Where the router comes to rest, once its navigation has finished
async function settled(router: ReturnType<typeof createMemoryRouter>) {
  const done = () => router.state.initialized && router.state.navigation.state === 'idle'
  if (!done()) {
    await new Promise<void>((resolve) => {
      const stop = router.subscribe(() => {
        if (done()) {
          stop()
          resolve()
        }
      })
    })
  }
  return router.state
}

afterEach(() => {
  vi.restoreAllMocks()
  queryClient.clear()
  held.signIn = Promise.resolve({ error: null })
})

it('says who may open every page in the table', () => {
  expect(paths(routes).sort()).toEqual(Object.keys(opens).sort())
})

it.each(Object.keys(opens).flatMap((path) => visits.map((visit) => [path, visit.who, visit] as const)))(
  '%s, opened by %s',
  async (path, _, visit) => {
    arrive(visit)
    const router = createMemoryRouter(routes, { initialEntries: [address(path)] })

    const state = await settled(router)

    const allowed = opens[path] === visit.is
    expect(state.location.pathname).toBe(allowed ? address(path) : home[visit.is])
    // Sent away, the address is replaced, so Back doesn't return to a page that sends them away again
    if (!allowed) expect(state.historyAction).toBe('REPLACE')
    router.dispose()
  },
)

it.each(visits.map((visit) => [visit.who, visit] as const))('/ sends %s home', async (_, visit) => {
  arrive(visit)
  const router = createMemoryRouter(routes, { initialEntries: ['/'] })

  const state = await settled(router)

  expect(state.location.pathname).toBe(home[visit.is])
  expect(state.historyAction).toBe('REPLACE')
  router.dispose()
})

it('asks who is visiting again once Finish Setup has refreshed it', async () => {
  arrive({ who: 'Ilvane', is: 'onboarding', me: () => answer(ilvane) })
  const router = createMemoryRouter(routes, { initialEntries: ['/onboarding'] })
  await settled(router)

  // She finishes setup: the API now says so, and Finish Setup refreshes what it changed
  network.mockImplementation(async () => answer({ ...ilvane, onboarding_complete: true }))
  await refresh.setupFinished()
  await router.navigate('/plan')

  expect(router.state.location.pathname).toBe('/plan')
  router.dispose()
})

it('waits for a sign-in in the address bar before deciding where the visitor belongs', async () => {
  let finish = () => {}
  held.signIn = new Promise((resolve) => {
    finish = () => resolve({ error: null })
  })
  const getSession = arrive({ who: 'Mbali', is: 'student', me: () => answer(mbali) })
  const router = createMemoryRouter(routes, { initialEntries: ['/?token_hash=made-up'] })

  // Until the link's token is swapped there is no session to ask about, so nothing may decide yet
  await new Promise((resolve) => setTimeout(resolve, 50))
  expect(getSession).not.toHaveBeenCalled()

  finish()
  expect((await settled(router)).location.pathname).toBe('/plan')
  router.dispose()
})
