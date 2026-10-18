// The one cache of what the API has answered, shared by every screen and by the guard
import { QueryClient } from '@tanstack/react-query'
import { ApiError } from './api.ts'

// The middleware in api.ts turns every failed request into an ApiError, so every query's and every
// mutation's error is typed as one
declare module '@tanstack/react-query' {
  interface Register {
    defaultError: ApiError
  }
}

// A read is tried again only when trying again could help: after a network failure, a timeout or a
// server error (5xx), never after a refusal (4xx). TanStack Query counts failures from 0 and waits 1,
// 2 and 4 seconds between tries, so this gives the error sheet's three retries with backoff. Writes
// keep TanStack Query's default of never retrying on their own: the API takes no idempotency key, so a
// retried write could save twice.
export function shouldRetry(failureCount: number, error: Error): boolean {
  if (!(error instanceof ApiError) || failureCount >= 3) return false
  return error.status === undefined || error.status >= 500
}

export const queryClient = new QueryClient({
  defaultOptions: {
    // Data changes only when the student acts, and each action refreshes what it changes
    // (queryKeys.ts), so nothing goes stale on a timer
    queries: { retry: shouldRetry, staleTime: Infinity },
  },
})
