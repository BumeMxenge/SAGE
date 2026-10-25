// A plan's credits and its slot card's words, written out by hand from the wording settled at Stop 1,
// with the counts on both sides of each plural and of "a" and "an"
import { expect, it } from 'vitest'
import { browse, creditsOf, fitting, lineNeeds } from './copy.ts'

it('adds the credits left to choose, and only when there are some', () => {
  expect(creditsOf(138, 18)).toBe('138 credits + 18 to choose')
  expect(creditsOf(156, 0)).toBe('156 credits')
})

it('says "an" before 8 and 18 credits, and "a" before 16', () => {
  expect(lineNeeds(18)).toBe('Add an 18-credit complementary studies course.')
  expect(lineNeeds(8)).toBe('Add an 8-credit complementary studies course.')
  expect(lineNeeds(16)).toBe('Add a 16-credit complementary studies course.')
})

it.each([
  [47, 35, '47 courses fit this plan, 35 of them need a check with your advisor.'],
  [47, 1, '47 courses fit this plan, 1 of them needs a check with your advisor.'],
  [47, 0, '47 courses fit this plan.'],
  [1, 1, '1 course fits this plan, and it needs a check with your advisor.'],
  [1, 0, '1 course fits this plan.'],
])('%i fitting, %i to check: %s', (fits, checks, words) => {
  expect(fitting(fits, checks)).toBe(words)
})

it('names the one course that fits, or how many do', () => {
  expect(browse(47)).toBe('Browse the 47 That Fit')
  expect(browse(1)).toBe('Browse the Course That Fits')
})
