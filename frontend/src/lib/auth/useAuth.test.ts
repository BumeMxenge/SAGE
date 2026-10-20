// Sign Out's promise that nothing read for one student stays in the page for whoever comes next. The
// cache keeps every read until then, so Sign Out is the only thing that empties it.
import { AuthRetryableFetchError } from '@supabase/supabase-js'
import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { queryClient } from '@/lib/queryClient.ts'
import { queries } from '@/lib/queryKeys.ts'
import { supabase } from '@/lib/supabase.ts'
import { useAuth } from './useAuth.ts'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  queryClient.clear()
})

// A logout request that gets no answer fails as this, and supabase-js drops the session all the same
it.each([
  ['succeeds', null],
  ['fails', new AuthRetryableFetchError('Failed to fetch', 0)],
] as const)('Sign Out empties the cache when the logout request %s', async (_, error) => {
  vi.spyOn(supabase.auth, 'signOut').mockResolvedValue({ error })
  queryClient.setQueryData(queries.history().queryKey, { cumulative_average: null, years: [] })
  const { result } = renderHook(() => useAuth())

  await act(() => result.current.signOut())

  expect(queryClient.getQueryCache().getAll()).toEqual([])
})
