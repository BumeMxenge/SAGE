// Two rules about her plan set as a whole: the plan that opens first, and the plan Compare puts beside
// the open one
import type { components } from '@/lib/api-types.ts'

type PlanSummary = components['schemas']['PlanSummary']

const byPosition = (plans: PlanSummary[]) => [...plans].sort((a, b) => a.position - b.position)

// The plan /plan opens: the first by position that her answers kept, or the first of all, should they
// have kept none
export function firstPlan(plans: PlanSummary[]): PlanSummary | undefined {
  const sorted = byPosition(plans)
  return sorted.find((plan) => !plan.hidden) ?? sorted.at(0)
}

// The plan Compare pairs with the open one: the next visible plan by position, round to the first
// after the last. With no other visible plan, as in a set of one, there's none, so Compare isn't shown.
export function partnerOf(plans: PlanSummary[], open: { id: string; position: number }): PlanSummary | undefined {
  const others = byPosition(plans).filter((plan) => plan.id !== open.id && !plan.hidden)
  return others.find((plan) => plan.position > open.position) ?? others.at(0)
}
