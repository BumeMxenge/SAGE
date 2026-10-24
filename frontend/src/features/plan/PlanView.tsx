// The plan view at /plan/:planId: a header with the plan switcher, the plan's credits and Compare, a row
// with the term and the view, Calendar or Course List, then the term's week or list. With ?compare=,
// two plans sit side by side in panels until Done Comparing, Back or Escape. The header and the term's
// row stay in view as the week scrolls beneath them. The address says which plans and term are open
// (lib/planAddress.ts), so choosing any of them changes it, and what was on screen stays there while
// the next plan arrives. While the sidebar and the assistant are both open, Compare, Done Comparing
// and the view's options show only their icons, each named in a tooltip, as the prototype's do when
// the docked assistant takes their room.
import { keepPreviousData, useQueries, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link } from 'react-aria-components'
import { useNavigate } from 'react-router'
import { Button } from '@/components/actions/Button/Button.tsx'
import { Card } from '@/components/content/Card/Card.tsx'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { Segment } from '@/components/inputs/SegmentedControl/Segment.tsx'
import { SegmentedControl } from '@/components/inputs/SegmentedControl/SegmentedControl.tsx'
import { Tooltip } from '@/components/overlays/Tooltip/Tooltip.tsx'
import { ApiError } from '@/lib/api.ts'
import { pageNames, termLabels } from '@/lib/copy.ts'
import { actionLabels, explain } from '@/lib/errors.ts'
import { type PlanAddress, planPath, planTerms, usePlanAddress } from '@/lib/planAddress.ts'
import { queries } from '@/lib/queryKeys.ts'
import { PlanSwitcher } from './components/PlanSwitcher/PlanSwitcher.tsx'
import { TermView, type View } from './components/TermView/TermView.tsx'
import { partnerOf } from './planSet.ts'
import { coloursOf, weekOf } from './week.ts'
import styles from './PlanView.module.css'

export function PlanView({ iconOnly }: { iconOnly: boolean }) {
  const address = usePlanAddress()
  const { planId, compareWith, term } = address
  const navigate = useNavigate()
  const [view, setView] = useState<View>('calendar')
  const { data: set } = useQuery(queries.plans())
  // Every plan in her set, read once, so each course keeps one colour in all of them
  const setPlans = useQueries({ queries: (set?.plans ?? []).map(({ id }) => queries.plan(id)) })
  // One plan, or two side by side. The read not on screen waits, and keeps what it had for Back.
  const single = useQuery({ ...queries.plan(planId), enabled: compareWith === null, placeholderData: keepPreviousData })
  const pair = useQuery({
    ...queries.comparison(planId, compareWith ?? planId),
    enabled: compareWith !== null,
    placeholderData: keepPreviousData,
  })

  // A new plan, a second plan or a term is a new address. A term replaces the address, so Back skips
  // the terms looked at.
  const go = (to: Partial<PlanAddress>, replace = false) => {
    void navigate(planPath({ ...address, ...to }), { replace })
  }

  // Escape leaves compare, as in the prototype, unless something open on the page takes it first, as
  // the plan list does to close
  useEffect(() => {
    if (compareWith === null) return
    const leave = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !event.defaultPrevented) void navigate(planPath({ planId, compareWith: null, term }))
    }
    window.addEventListener('keydown', leave)
    return () => window.removeEventListener('keydown', leave)
  }, [compareWith, navigate, planId, term])

  // A plan that was replaced, or an address that isn't one of hers (error case 14)
  const error = compareWith === null ? single.error : pair.error
  if (error instanceof ApiError && error.code === 'plan_not_found') {
    const { title, message } = explain(error)
    return (
      <ErrorState variant="page" icon="calendar_today" title={title} message={message}>
        <Link href="/plan">{actionLabels.go_to_plan}</Link>
      </ErrorState>
    )
  }
  // Nothing shows until her set and every plan in it arrive, then the plan, or in compare the panels
  // until both plans do. Their loading and error states come with the app's others.
  if (!set) return null
  const read = setPlans.flatMap(({ data }) => (data ? [data] : []))
  if (read.length < set.plans.length) return null
  // The set's plans by position, then those on screen, which a link can open from an earlier set
  const byPosition = read.sort((a, b) => a.position - b.position)
  // The plans her lists offer: those her answers kept, and any the assistant has offered since. A
  // plan they hid is in no list.
  const shown = set.plans.filter((summary) => !summary.hidden)

  const controls = (
    <div className={styles.controls}>
      <SegmentedControl
        label="Term"
        selectedKey={term}
        onChange={(key) => {
          const chosen = planTerms.find((each) => each === key)
          if (chosen) go({ term: chosen }, true)
        }}
      >
        {planTerms.map((each) => (
          <Segment key={each} id={each}>
            {termLabels[each]}
          </Segment>
        ))}
      </SegmentedControl>
      <SegmentedControl label="View" selectedKey={view} onChange={(key) => setView(key === 'list' ? 'list' : 'calendar')}>
        <Tooltip text="Calendar" isDisabled={!iconOnly}>
          <Segment id="calendar" icon={iconOnly ? 'calendar_today' : undefined}>
            Calendar
          </Segment>
        </Tooltip>
        <Tooltip text="Course List" isDisabled={!iconOnly}>
          <Segment id="list" icon={iconOnly ? 'format_list_bulleted' : undefined}>
            Course List
          </Segment>
        </Tooltip>
      </SegmentedControl>
    </div>
  )

  if (compareWith === null) {
    const plan = single.data
    if (!plan) return null
    const week = weekOf(plan, term)
    // A plan from an earlier set, or one her answers hid, opened from a link or her history, isn't one
    // to switch between, so it shows its name alone
    const switchable = shown.length > 1 && shown.some((summary) => summary.id === plan.id)
    const partner = partnerOf(set.plans, plan)
    return (
      <>
        <div className={styles.bar}>
          <div className={styles.header}>
            <h1 className="visually-hidden">{pageNames.plan}</h1>
            {switchable ? (
              <PlanSwitcher
                label="Plan"
                variant="outlined"
                plans={shown}
                selected={plan.id}
                onChange={(chosen) => go({ planId: chosen })}
              />
            ) : (
              <p className={styles.name}>{plan.name}</p>
            )}
            <p className={styles.credits}>{plan.credits.total} credits</p>
            {partner && (
              <Tooltip text="Compare" isDisabled={!iconOnly}>
                <Button
                  variant="secondary"
                  icon="view_column_2"
                  iconOnly={iconOnly}
                  onPress={() => go({ compareWith: partner.id })}
                >
                  Compare
                </Button>
              </Tooltip>
            )}
          </div>
          {controls}
        </div>
        <TermView plan={plan} term={term} view={view} week={week} colours={coloursOf([...byPosition, plan])} />
      </>
    )
  }

  const bar = (
    <div className={styles.bar}>
      <div className={styles.header}>
        <h1 className={styles.title}>Comparing Plans</h1>
        <Tooltip text="Done Comparing" isDisabled={!iconOnly}>
          <Button variant="secondary" icon="close" iconOnly={iconOnly} onPress={() => go({ compareWith: null })}>
            Done Comparing
          </Button>
        </Tooltip>
      </div>
      {controls}
    </div>
  )
  const comparison = pair.data
  if (!comparison) return bar
  const { first, second } = comparison
  const firstWeek = weekOf(first, term)
  const secondWeek = weekOf(second, term)
  const colours = coloursOf([...byPosition, first, second])
  // Another plan to swap in for the second, when the set has one beyond these two
  const swappable = shown.some((summary) => summary.id !== first.id && summary.id !== second.id)
  return (
    <>
      {bar}
      <div className={styles.panels}>
        <Card title={first.name} level={2} meta={<p className={styles.panelCredits}>{first.credits.total} credits</p>}>
          <TermView plan={first} term={term} view={view} week={firstWeek} colours={colours} compact />
        </Card>
        <Card
          title={second.name}
          level={2}
          meta={<p className={styles.panelCredits}>{second.credits.total} credits</p>}
          actions={
            swappable && (
              <PlanSwitcher
                label="Compare with Another Plan"
                variant="quiet"
                plans={shown.filter((summary) => summary.id !== first.id)}
                selected={second.id}
                onChange={(chosen) => go({ compareWith: chosen })}
              />
            )
          }
        >
          <TermView plan={second} term={term} view={view} week={secondWeek} colours={colours} compact />
        </Card>
      </div>
    </>
  )
}
