// The filtered page's line, written out by hand, with the count on both sides of the plural
import { expect, it } from 'vitest'
import { showing } from './copy.ts'

it('says one course fits, and two courses fit', () => {
  expect(showing(1, 'Signals, Power & Robotics')).toBe('Showing the 1 course that fits Signals, Power & Robotics.')
  expect(showing(2, 'Signals, Power & Robotics')).toBe('Showing the 2 courses that fit Signals, Power & Robotics.')
})
