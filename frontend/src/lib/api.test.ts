// @vitest-environment node
// What a request reaches its caller as when it fails. Each request goes through the real client and
// its middleware, with a made-up answer in place of the network. It runs in Node, because Node's
// Request refuses jsdom's AbortSignal.
import type { Session } from '@supabase/supabase-js'
import { afterEach, expect, it, vi } from 'vitest'
import { ApiError, client, dataOf, type Problem } from './api.ts'
import { supabase } from './supabase.ts'

afterEach(() => {
  vi.restoreAllMocks()
})

it('brings a refusal back as its code, with its status and extra fields, from a signed request', async () => {
  vi.spyOn(supabase.auth, 'getSession').mockResolvedValue({
    data: { session: { access_token: 'made-up-token' } as Session },
    error: null,
  })
  // A made-up refusal, written out in the shape backend/src/sage/shared/api/problems.py sends
  const notYours: Problem = {
    type: 'about:blank',
    title: 'Unprocessable Content',
    status: 422,
    detail: 'This transcript belongs to another student.',
    code: 'transcript_not_yours',
    transcript_student_number: 'DLMMBA999',
    account_student_number: 'QRTILV999',
  }
  let sent: Request | undefined
  // The transcript goes as the PDF itself, the way lib/api.ts tells its caller to send it, and through
  // dataOf, as a screen's write does
  const error: unknown = await dataOf(
    client.POST('/v1/onboarding/transcript', {
      body: new File(['%PDF-1.4 made up'], 'transcript.pdf') as unknown as string,
      bodySerializer: (body) => body,
      headers: { 'Content-Type': 'application/pdf' },
      fetch: async (request) => {
        sent = request
        return new Response(JSON.stringify(notYours), {
          status: 422,
          headers: { 'Content-Type': 'application/problem+json' },
        })
      },
    }),
  ).catch((thrown: unknown) => thrown)

  expect(error).toBeInstanceOf(ApiError)
  expect(error).toMatchObject({
    code: 'transcript_not_yours',
    status: 422,
    problem: { transcript_student_number: 'DLMMBA999', account_student_number: 'QRTILV999' },
  })
  // The middleware's time limit wraps the request, and the token, the type and the PDF survive it
  expect(sent?.headers.get('Authorization')).toBe('Bearer made-up-token')
  expect(sent?.headers.get('Content-Type')).toBe('application/pdf')
  expect(await sent?.text()).toBe('%PDF-1.4 made up')
})

it.each([
  ['no answer', () => Promise.reject(new TypeError('fetch failed')), 'network_error', undefined],
  ['no answer in time', () => Promise.reject(new DOMException('Timed out', 'TimeoutError')), 'timeout', undefined],
  [
    'an error page from in front of the API',
    () => Promise.resolve(new Response('<h1>Bad Gateway</h1>', { status: 502, headers: { 'Content-Type': 'text/html' } })),
    'server_unavailable',
    502,
  ],
])('brings %s back as its own code', async (_, answer, code, status) => {
  const error: unknown = await client.GET('/v1/plans', { fetch: answer }).catch((thrown: unknown) => thrown)

  expect(error).toBeInstanceOf(ApiError)
  expect(error).toMatchObject({ code, status })
})
