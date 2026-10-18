import { expect, it } from 'vitest'
import { ApiError } from './api.ts'
import { shouldRetry } from './queryClient.ts'

// TanStack Query asks after each failure, counting from 0, so 2 allows the third retry and 3 stops a
// fourth: the error sheet's "up to three times"
it.each([
  ['a network failure', new ApiError('network_error')],
  ['a timeout', new ApiError('timeout')],
  ['a server error', new ApiError('internal_error', 500)],
  ['an error page from in front of the API', new ApiError('server_unavailable', 503)],
])('retries a read after %s three times, and no more', (_, error) => {
  expect(shouldRetry(2, error)).toBe(true)
  expect(shouldRetry(3, error)).toBe(false)
})

it.each([
  ['not_signed_in', 401],
  ['plan_not_found', 404],
  ['plans_not_ready', 409],
  ['transcript_not_yours', 422],
] as const)('never retries a refusal: %s', (code, status) => {
  expect(shouldRetry(0, new ApiError(code, status))).toBe(false)
})
