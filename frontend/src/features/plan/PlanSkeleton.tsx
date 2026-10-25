// The plan's skeleton at /plan, before any plan is open: while her set is read, while her answers to
// the questionnaire save, and while the guard decides on the first load. Most students land on a plan
// from here, so it draws loading case 01, as the plan view does while its plan arrives: the term and
// view render straight away, and the plan's name, credits, Compare and week are skeletons. /plan has no
// assistant, so the skeleton keeps the folded strip's place clear, and the strip draws into it as her
// plan opens, moving nothing. The term and view are the plan workspace's, so the plan opens in those
// chosen here.
import { pageNames } from '@/lib/copy.ts'
import type { PlanTerm } from '@/lib/planAddress.ts'
import { PlanBar } from './components/PlanBar/PlanBar.tsx'
import { PlanHeaderSkeleton } from './components/PlanBar/PlanHeaderSkeleton.tsx'
import { TermView, type View } from './components/TermView/TermView.tsx'
import styles from './PlanSkeleton.module.css'

// What a screen reader hears while a plan is on its way
export const loadingPlan = 'Loading your plan…'

type PlanSkeletonProps = {
  term: PlanTerm
  onTermChange: (term: PlanTerm) => void
  view: View
  onViewChange: (view: View) => void
  iconOnly: boolean
}

export function PlanSkeleton({ term, onTermChange, view, onViewChange, iconOnly }: PlanSkeletonProps) {
  return (
    <div className={styles.planSkeleton}>
      <PlanBar term={term} onTermChange={onTermChange} view={view} onViewChange={onViewChange} iconOnly={iconOnly}>
        <h1 className="visually-hidden">{pageNames.plan}</h1>
        <PlanHeaderSkeleton />
      </PlanBar>
      <TermView plan={null} view={view} />
      <output className="visually-hidden">{loadingPlan}</output>
    </div>
  )
}
