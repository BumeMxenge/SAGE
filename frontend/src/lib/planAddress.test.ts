// The plan's address, read and written in one place. The paths are written out by hand.
import { describe, expect, it } from 'vitest'
import { planPath, previewPath, readAddress } from './planAddress.ts'

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
    const asked = { planId: 'p1', compareWith: 'p2', term: 'sem2', preview: null } as const
    const path = planPath(asked)
    expect(path).toBe('/plan/p1?compare=p2&term=sem2')
    expect(readAddress('p1', query(path.split('?')[1]))).toEqual(asked)
    expect(planPath({ planId: 'p1', compareWith: null, term: 'sem1', preview: null })).toBe('/plan/p1')
  })

  it('keeps a preview and its term, and reads back as the same address', () => {
    const asked = { planId: 'p1', compareWith: null, term: 'sem2', preview: 'SLL1002S' } as const
    const path = planPath(asked)
    expect(path).toBe('/plan/p1?preview=SLL1002S&term=sem2')
    expect(readAddress('p1', query(path.split('?')[1]))).toEqual(asked)
  })

  it('opens compare, with no preview, when the address asks for both', () => {
    expect(readAddress('p1', query('compare=p2&preview=SLL1002S'))).toMatchObject({ compareWith: 'p2', preview: null })
    expect(planPath({ planId: 'p1', compareWith: 'p2', term: 'sem1', preview: 'SLL1002S' })).toBe('/plan/p1?compare=p2')
  })

  it("previews a course on its semester's tab, a quarter's and a full year's included", () => {
    expect(previewPath('p1', 'SLL1002S', 'sem2')).toBe('/plan/p1?preview=SLL1002S&term=sem2')
    expect(previewPath('p1', 'TST1001F', 'q2')).toBe('/plan/p1?preview=TST1001F')
    expect(previewPath('p1', 'TST1002W', 'full_year')).toBe('/plan/p1?preview=TST1002W')
  })
})
