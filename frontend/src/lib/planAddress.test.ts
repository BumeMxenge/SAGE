// The plan's address, read and written in one place. The paths are written out by hand.
import { describe, expect, it } from 'vitest'
import { planPath, readAddress } from './planAddress.ts'

const query = (search: string) => new URLSearchParams(search)

describe('a plan address', () => {
  it('opens Sem 1 when it names no term, or a term SAGE has no tab for', () => {
    expect(readAddress('p1', query('')).term).toBe('sem1')
    expect(readAddress('p1', query('term=q3')).term).toBe('sem1')
    expect(readAddress('p1', query('term=winter')).term).toBe('winter')
  })

  it('opens the plan alone when it compares the plan with itself, or with nothing', () => {
    expect(readAddress('p1', query('compare=p1')).compareWith).toBeNull()
    expect(readAddress('p1', query('compare=')).compareWith).toBeNull()
    expect(readAddress('p1', query('compare=p2')).compareWith).toBe('p2')
  })

  it('keeps the plan it compares with and its term, and reads back as the same address', () => {
    const asked = { planId: 'p1', compareWith: 'p2', term: 'sem2' } as const
    const path = planPath(asked)
    expect(path).toBe('/plan/p1?compare=p2&term=sem2')
    expect(readAddress('p1', query(path.split('?')[1]))).toEqual(asked)
    expect(planPath({ planId: 'p1', compareWith: null, term: 'sem1' })).toBe('/plan/p1')
  })
})
