// The plan view at /plan/:planId: a header with the plan switcher and the plan's credits, a row with
// the term and the view, Calendar or Course List, then the term's week or list. The header and that
// row stay in view as the week scrolls beneath them. The address says which plan and term are open
// (lib/planAddress.ts), so choosing either changes it, and the last plan stays on screen while the
// next one arrives.
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-aria-components'
import { useNavigate } from 'react-router'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { Segment } from '@/components/inputs/SegmentedControl/Segment.tsx'
import { SegmentedControl } from '@/components/inputs/SegmentedControl/SegmentedControl.tsx'
import { ApiError } from '@/lib/api.ts'
import { pageNames, termLabels } from '@/lib/copy.ts'
import { actionLabels, explain } from '@/lib/errors.ts'
import { type PlanAddress, planPath, planTerms, usePlanAddress } from '@/lib/planAddress.ts'
import { queries } from '@/lib/queryKeys.ts'
import { PlanSwitcher } from './components/PlanSwitcher/PlanSwitcher.tsx'
import { TermView, type View } from './components/TermView/TermView.tsx'
import { coloursOf, weekOf } from './week.ts'
import styles from './PlanView.module.css'

// A plan on its own has no other to differ from
const alone: ReadonlySet<string> = new Set()

export function PlanView() {
  const address = usePlanAddress()
  const navigate = useNavigate()
  const [view, setView] = useState<View>('calendar')
  const { data: set } = useQuery(queries.plans())
  const { data: plan, error } = useQuery({ ...queries.plan(address.planId), placeholderData: keepPreviousData })

  // A new plan or term is a new address. A term replaces the address, so Back skips the terms looked at.
  const go = (to: Partial<PlanAddress>, replace = false) => {
    void navigate(planPath({ ...address, ...to }), { replace })
  }

  // A plan that was replaced, or an address that isn't one of hers (error case 14)
  if (error instanceof ApiError && error.code === 'plan_not_found') {
    const { title, message } = explain(error)
    return (
      <ErrorState variant="page" icon="calendar_today" title={title} message={message}>
        <Link href="/plan">{actionLabels.go_to_plan}</Link>
      </ErrorState>
    )
  }
  // Nothing shows until the plan and her set arrive. Their loading and error states come with the app's
  // others.
  if (!set || !plan) return null

  const week = weekOf(plan, address.term)
  // A plan from an earlier set, opened from a link, isn't one of this set's to switch between
  const switchable = set.plans.length > 1 && set.plans.some((summary) => summary.id === plan.id)
  return (
    <>
      <div className={styles.bar}>
        <div className={styles.header}>
          <h1 className="visually-hidden">{pageNames.plan}</h1>
          {switchable ? (
            <PlanSwitcher
              label="Plan"
              variant="outlined"
              plans={set.plans}
              selected={plan.id}
              onChange={(planId) => go({ planId })}
            />
          ) : (
            <p className={styles.name}>{plan.name}</p>
          )}
          <p className={styles.credits}>{plan.credits.total} credits</p>
        </div>
        <div className={styles.controls}>
          <SegmentedControl
            label="Term"
            selectedKey={address.term}
            onChange={(key) => {
              const term = planTerms.find((each) => each === key)
              if (term) go({ term }, true)
            }}
          >
            {planTerms.map((term) => (
              <Segment key={term} id={term}>
                {termLabels[term]}
              </Segment>
            ))}
          </SegmentedControl>
          <SegmentedControl label="View" selectedKey={view} onChange={(key) => setView(key === 'list' ? 'list' : 'calendar')}>
            <Segment id="calendar">Calendar</Segment>
            <Segment id="list">Course List</Segment>
          </SegmentedControl>
        </div>
      </div>
      <TermView plan={plan} term={address.term} view={view} week={week} colours={coloursOf([week])} only={alone} />
    </>
  )
}
