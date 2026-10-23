// Which plan is open, and how, as the page's address says: /plan/:planId opens one plan,
// ?compare=:otherId puts a second beside it, and ?term= picks the term on screen, Sem 1 when it names
// none. The address is the one record of these, so Back, a reload and a link from the chat all land in
// the same place. Every screen that reads or writes them goes through here.
import { useParams, useSearchParams } from 'react-router'
import type { components } from './api-types.ts'

type TermCode = components['schemas']['Meeting']['term']

// The terms a plan shows, a tab each. Quarter and full-year courses sit inside the semesters.
export const planTerms = ['sem1', 'sem2', 'winter', 'summer'] as const satisfies readonly TermCode[]
export type PlanTerm = (typeof planTerms)[number]

export type PlanAddress = { planId: string; compareWith: string | null; term: PlanTerm }

// What a plan's address asks for. A term it doesn't know opens Sem 1, and a plan compared with itself
// opens alone, as the API refuses that pair.
export function readAddress(planId: string, query: URLSearchParams): PlanAddress {
  const term = planTerms.find((each) => each === query.get('term')) ?? 'sem1'
  const compare = query.get('compare')
  return { planId, compareWith: compare && compare !== planId ? compare : null, term }
}

export function usePlanAddress(): PlanAddress {
  const { planId } = useParams()
  const [query] = useSearchParams()
  // Only a plan's own address names one, and only the pages at it ask
  if (!planId) throw new Error('usePlanAddress reads /plan/:planId')
  return readAddress(planId, query)
}

// The address that opens a plan as asked. Sem 1 is left out, as an address without a term opens it.
export function planPath({ planId, compareWith, term }: PlanAddress): string {
  const query = new URLSearchParams()
  if (compareWith) query.set('compare', compareWith)
  if (term !== 'sem1') query.set('term', term)
  const search = query.toString()
  return search ? `/plan/${planId}?${search}` : `/plan/${planId}`
}
