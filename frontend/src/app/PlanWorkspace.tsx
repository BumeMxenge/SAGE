// The plan workspace. While her set is too long to compare and isn't answered, /plan shows the
// questionnaire. Then /plan opens her first plan, replacing its own address so Back never returns to
// it, or says why she has none. A plan's own address shows the plan view, with the assistant beside it
// in the frame, and while the sidebar and the assistant are both open the plan's controls show only
// their icons. Until her set arrives, /plan shows the plan's skeleton, as most students land on a
// plan, and the questionnaire gives way to it while her answers save. Once /plan has shown it, it stays
// while her first plan opens, so nothing blanks between them. A term picked there goes into /plan's
// address, as on a plan's own, and her first plan opens in it. Held, as the route table draws it while
// the guard decides on the first load, it reads nothing and shows only its skeleton.
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Navigate, useOutletContext, useParams, useSearchParams } from 'react-router'
import { EmptyState } from '@/components/feedback/EmptyState/EmptyState.tsx'
import { PlanSkeleton } from '@/features/plan/PlanSkeleton.tsx'
import { PlanView } from '@/features/plan/PlanView.tsx'
import { firstPlan } from '@/features/plan/planSet.ts'
import { QuestionnairePage } from '@/features/questionnaire/QuestionnairePage.tsx'
import { pageNames } from '@/lib/copy.ts'
import { planPath, planTerms } from '@/lib/planAddress.ts'
import { queries } from '@/lib/queryKeys.ts'
import type { PageRoom } from './AppLayout.tsx'

export function PlanWorkspace({ held = false }: { held?: boolean }) {
  const { planId } = useParams()
  const [query, setQuery] = useSearchParams()
  const room = useOutletContext<PageRoom>()
  const read = useQuery({ ...queries.plans(), enabled: !held })
  // Whether /plan has shown the plan's skeleton, or the questionnaire, which gives way to it
  const [waited, setWaited] = useState(false)
  if (planId) return <PlanView {...room} held={held} />
  // Read as a plan's own address reads it, Sem 1 when it names none, and replaced, as there
  const term = planTerms.find((each) => each === query.get('term')) ?? 'sem1'
  const skeleton = (
    <PlanSkeleton
      {...room}
      term={term}
      onTermChange={(chosen) => setQuery(chosen === 'sem1' ? {} : { term: chosen }, { replace: true })}
    />
  )
  // Held, what the frame's assistant may already have read doesn't count
  const set = held ? undefined : read.data
  if (!set) {
    // A read that failed shows nothing, until the app's error states come
    if (read.isError) return null
    if (!waited) setWaited(true)
    return skeleton
  }
  if (set.questionnaire_needed) {
    if (!waited) setWaited(true)
    return <QuestionnairePage set={set} saving={skeleton} />
  }
  const first = firstPlan(set.plans)
  if (first) {
    return (
      <>
        <Navigate replace to={planPath({ planId: first.id, compareWith: null, term, preview: null })} />
        {waited && skeleton}
      </>
    )
  }
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
