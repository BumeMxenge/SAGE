// The words an error shows, for a failure in the browser and for one the API explained
import { expect, it } from 'vitest'
import { ApiError } from './api.ts'
import { explain } from './errors.ts'

it('gives a failure in the browser words of its own, which ask for no reference', () => {
  expect(explain(new TypeError('Failed to fetch dynamically imported module'))).toEqual({
    title: 'Something Went Wrong',
    message: 'SAGE ran into a problem on this page. Reload it and try again.',
    action: 'retry',
    reference: undefined,
  })
})

it('keeps the reference of a failure the API explained, which its words ask her to quote', () => {
  const problem = {
    type: 'about:blank',
    title: 'Made Up',
    status: 500,
    detail: 'A made-up failure.',
    code: 'internal_error',
    reference: 'SG-0000-MADE',
  } as const
  const { message, reference } = explain(new ApiError('internal_error', 500, problem))
  expect(message).toContain('quote the reference')
  expect(reference).toBe('SG-0000-MADE')
})
