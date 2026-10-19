// Microsoft is asked for an account's name once, however many screens ask at the same time, and not at
// all once this browser keeps the name. The names are Mbali's, the made-up student's.
import { afterEach, expect, it, vi } from 'vitest'
import { keepName, lookUpName } from './name.ts'

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
})

it('asks Graph once for an account however many screens ask, and not at all for a kept name', async () => {
  const graph = vi.fn(async () => Response.json({ givenName: 'Mbali', surname: 'Dlamini' }))
  vi.stubGlobal('fetch', graph)
  const asked = await Promise.all([lookUpName('first-account', 'a-token'), lookUpName('first-account', 'a-token')])
  expect(asked).toEqual([
    { givenName: 'Mbali', surname: 'Dlamini' },
    { givenName: 'Mbali', surname: 'Dlamini' },
  ])
  keepName('second-account', { givenName: 'Mbali', surname: 'Dlamini' })
  expect(await lookUpName('second-account', 'a-token')).toEqual({ givenName: 'Mbali', surname: 'Dlamini' })
  expect(graph).toHaveBeenCalledTimes(1)
})
