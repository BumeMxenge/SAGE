// Which plan is open, and how, as the page's address says: /plan/:planId opens one plan,
// ?compare=:otherId puts a second beside it, ?preview=:code draws one course in the plan's
// complementary slot without saving it, and ?term= picks the term on screen, Sem 1 when it names
// none. The address is the one record of these, so Back, a reload and a link from the chat all land in
// the same place. Every screen that reads or writes them goes through here.
import { useParams, useSearchParams } from 'react-router'
import type { components } from './api-types.ts'

type TermCode = components['schemas']['Meeting']['term']

// The terms a plan shows, a tab each. Quarter and full-year courses sit inside the semesters.
export const planTerms = ['sem1', 'sem2', 'winter', 'summer'] as const satisfies readonly TermCode[]
export type PlanTerm = (typeof planTerms)[number]

// The tabs a term shows under: a quarter inside its semester, a full-year course in both semesters,
// and practical training's "other" in none
const tabsOf: Record<TermCode, readonly PlanTerm[]> = {
  q1: ['sem1'],
  q2: ['sem1'],
  sem1: ['sem1'],
  q3: ['sem2'],
  q4: ['sem2'],
  sem2: ['sem2'],
  full_year: ['sem1', 'sem2'],
  winter: ['winter'],
  summer: ['summer'],
  other: [],
}

export const inTerm = (term: TermCode, tab: PlanTerm) => tabsOf[term].includes(tab)

export type PlanAddress = { planId: string; compareWith: string | null; term: PlanTerm; preview: string | null }

// What a plan's address asks for. A term it doesn't know opens Sem 1, and a plan compared with itself
// opens alone, as the API refuses that pair. A preview opens only on a plan alone, so an address with
// both opens compare.
export function readAddress(planId: string, query: URLSearchParams): PlanAddress {
  const term = planTerms.find((each) => each === query.get('term')) ?? 'sem1'
  const compare = query.get('compare')
  const compareWith = compare && compare !== planId ? compare : null
  return { planId, compareWith, term, preview: compareWith ? null : query.get('preview') || null }
}

export function usePlanAddress(): PlanAddress {
  const { planId } = useParams()
  const [query] = useSearchParams()
  // Only a plan's own address names one, and only the pages at it ask
  if (!planId) throw new Error('usePlanAddress reads /plan/:planId')
  return readAddress(planId, query)
}

// The address that opens a plan as asked. Sem 1 is left out, as an address without a term opens it.
export function planPath({ planId, compareWith, term, preview }: PlanAddress): string {
  const query = new URLSearchParams()
  if (compareWith) query.set('compare', compareWith)
  else if (preview) query.set('preview', preview)
  if (term !== 'sem1') query.set('term', term)
  const search = query.toString()
  return search ? `/plan/${planId}?${search}` : `/plan/${planId}`
}

// The address that previews one offering of a complementary course in a plan, on the first term it
// shows under
export const previewPath = (planId: string, code: string, term: TermCode) =>
  planPath({ planId, compareWith: null, term: tabsOf[term].at(0) ?? 'sem1', preview: code })
