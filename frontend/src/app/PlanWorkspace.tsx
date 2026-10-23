// The plan workspace. While her set is too long to compare and isn't answered, /plan shows the
// questionnaire. Then /plan opens her first plan, replacing its own address so Back never returns to
// it, or says why she has none. A plan's own address shows the plan view, and the assistant will sit
// beside it.
import { useQuery } from '@tanstack/react-query'
import { Navigate, useParams } from 'react-router'
import { EmptyState } from '@/components/feedback/EmptyState/EmptyState.tsx'
import { PlanView } from '@/features/plan/PlanView.tsx'
import { firstPlan } from '@/features/plan/planSet.ts'
import { QuestionnairePage } from '@/features/questionnaire/QuestionnairePage.tsx'
import { pageNames } from '@/lib/copy.ts'
import { planPath } from '@/lib/planAddress.ts'
import { queries } from '@/lib/queryKeys.ts'

export function PlanWorkspace() {
  const { planId } = useParams()
  const { data: set } = useQuery(queries.plans())
  if (planId) return <PlanView />
  // Nothing shows until her plans arrive. Its loading state comes with the app's others.
  if (!set) return null
  if (set.questionnaire_needed) return <QuestionnairePage set={set} />
  const first = firstPlan(set.plans)
  if (first) return <Navigate replace to={planPath({ planId: first.id, compareWith: null, term: 'sem1' })} />
  // A set with no plan, as for a student who has finished, or one nothing fits: the set says why
  return (
    <>
      <h1 className="visually-hidden">{pageNames.plan}</h1>
      <EmptyState
        title={`No Plans for ${set.period}`}
        message={set.reasons.map((reason) => reason.message).join(' ') || 'SAGE found no plan that fits your record.'}
      />
    </>
  )
}
