import { QueryObserver } from '@tanstack/react-query'
import { afterEach, expect, it, vi } from 'vitest'
import { ApiError } from './api.ts'
import { queryClient, shouldRetry } from './queryClient.ts'

afterEach(() => {
  vi.useRealTimers()
  queryClient.clear()
})

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
] as const)('never retries a refusal: %s', (code, status) => {
  expect(shouldRetry(0, new ApiError(code, status))).toBe(false)
})

// A page reads through an observer, which goes when the page closes. TanStack Query's default would
// drop the read five minutes later, and the page would wait for the API again when it reopened.
it('keeps a read after its page closes, however long the student is away', async () => {
  vi.useFakeTimers()
  const page = new QueryObserver(queryClient, { queryKey: ['a read'], queryFn: () => 'the answer' })
  const close = page.subscribe(() => undefined)
  await vi.advanceTimersByTimeAsync(0) // the answer arrives
  close()

  await vi.advanceTimersByTimeAsync(24 * 60 * 60 * 1000) // a day on other pages, or in other tabs

  expect(queryClient.getQueryData(['a read'])).toBe('the answer')
})
