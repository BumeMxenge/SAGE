// Explore Electives' address, read and written in one place. The paths are written out by hand.
import { describe, expect, it } from 'vitest'
import { electivesPath, readElectivesAddress } from './electivesAddress.ts'

const query = (search: string) => new URLSearchParams(search)

describe("Explore Electives' address", () => {
  it('names no plan or tab when it gives none, or gives them empty', () => {
    expect(readElectivesAddress(query(''))).toEqual({ planId: null, tab: null })
    expect(readElectivesAddress(query('plan=&tab='))).toEqual({ planId: null, tab: null })
  })

  it('keeps the plan when the tab changes, and reads back as the same address', () => {
    const asked = { planId: 'p1', tab: 'languages' }
    const path = electivesPath(asked)
    expect(path).toBe('/electives?plan=p1&tab=languages')
    expect(readElectivesAddress(query(path.split('?')[1]))).toEqual(asked)
    expect(electivesPath({ planId: 'p1', tab: null })).toBe('/electives?plan=p1')
    expect(electivesPath({ planId: null, tab: null })).toBe('/electives')
  })
})
