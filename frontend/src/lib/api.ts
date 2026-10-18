// Calls to the SAGE backend (FastAPI). openapi-fetch reads every path, request and response from
// api-types.ts, so no endpoint needs request code of its own. One middleware signs every request in,
// gives it a time limit and turns every failure into an ApiError, so each screen handles one kind of
// error.
//
// POST /v1/onboarding/transcript takes the PDF itself, not a form. api-types.ts types that body as a
// string, which is how openapi-typescript reads format: binary, so its caller passes the File with
// body: file as unknown as string, bodySerializer: (body) => body, and the header Content-Type:
// application/pdf. Otherwise openapi-fetch would send the File as JSON, which is {}.
import createFetchClient, { type Middleware } from 'openapi-fetch'
import type { components, paths } from './api-types.ts'
import { env } from './env.ts'
import { supabase } from './supabase.ts'

export type Problem = components['schemas']['Problem']

// The ways a request can fail before the API can explain why: no connection, no answer in time, or an
// error page from something in front of the API, such as Azure's gateway while the backend restarts
type ClientCode = 'network_error' | 'timeout' | 'server_unavailable'
export type ErrorCode = components['schemas']['Code'] | ClientCode

// A request that didn't succeed: a refusal the API explained, or a failure on the way there
export class ApiError extends Error {
  readonly code: ErrorCode
  readonly status: number | undefined // none when no answer came back
  readonly problem: Problem | undefined // the refusal in full: its detail, reference and extra fields

  constructor(code: ErrorCode, status?: number, problem?: Problem) {
    super(problem?.detail ?? code)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.problem = problem
  }
}

// How long a request may take before it fails as a timeout. Writes may take longer: the transcript
// upload, and the advisor's replies.
const readLimitMs = 20_000
const writeLimitMs = 60_000

const middleware: Middleware = {
  async onRequest({ request }) {
    const { data } = await supabase.auth.getSession()
    if (data.session) request.headers.set('Authorization', `Bearer ${data.session.access_token}`)
    const limit = request.method === 'GET' ? readLimitMs : writeLimitMs
    // TanStack Query's own signal still cancels it, as when the screen that asked closes
    return new Request(request, { signal: AbortSignal.any([request.signal, AbortSignal.timeout(limit)]) })
  },
  async onResponse({ response }) {
    if (response.ok) return undefined
    if (response.headers.get('Content-Type')?.startsWith('application/problem+json')) {
      const problem = (await response.json()) as Problem
      throw new ApiError(problem.code, response.status, problem)
    }
    throw new ApiError('server_unavailable', response.status)
  },
  onError({ error }) {
    // fetch fails with a TypeError when it gets no answer: no connection, a refused connection, or CORS
    if (error instanceof TypeError) return new ApiError('network_error')
    if (error instanceof DOMException && error.name === 'TimeoutError') return new ApiError('timeout')
    return undefined // a cancelled request stays cancelled, which TanStack Query expects
  },
}

export const client = createFetchClient<paths>({ baseUrl: env.apiUrl })
client.use(middleware)
