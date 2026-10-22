// The plan that opens first and the plan Compare pairs with the open one, on made-up sets listed out
// of order. Each expected plan is worked out by hand in its comment.
import { describe, expect, it } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { firstPlan, partnerOf } from './planSet.ts'

type PlanSummary = components['schemas']['PlanSummary']

const summary = (position: number, hidden = false): PlanSummary => ({
  id: `p${position}`,
  position,
  name: `Plan ${position}`,
  combination: null,
  hidden,
  credits: 138,
})

describe('the plan /plan opens', () => {
  it('is the first by position that her answers kept', () => {
    // Listed 3, 1, 2, with 1 hidden: 2 is the first kept
    expect(firstPlan([summary(3), summary(1, true), summary(2)])?.id).toBe('p2')
  })

  it('is the first of all when her answers kept none, and none in an empty set', () => {
    expect(firstPlan([summary(2, true), summary(1, true)])?.id).toBe('p1')
    expect(firstPlan([])).toBeUndefined()
  })
})

describe('the plan Compare pairs with the open one', () => {
  // Listed out of order: 1 and 3 visible, 2 hidden
  const set = [summary(3), summary(2, true), summary(1)]

  it('is the next visible plan, round to the first after the last', () => {
    // From 1 the next visible is 3, as 2 is hidden
    expect(partnerOf(set, { id: 'p1', position: 1 })?.id).toBe('p3')
    // 3 is the last, so round to 1
    expect(partnerOf(set, { id: 'p3', position: 3 })?.id).toBe('p1')
    // The hidden 2, opened from a link, pairs with the next visible, 3
    expect(partnerOf(set, { id: 'p2', position: 2 })?.id).toBe('p3')
  })

  it('is a hidden plan when no other is visible, and none in a set of one', () => {
    expect(partnerOf([summary(1), summary(2, true)], { id: 'p1', position: 1 })?.id).toBe('p2')
    expect(partnerOf([summary(1)], { id: 'p1', position: 1 })).toBeUndefined()
  })
})
