// The plan view at /plan/:planId: a header with the plan switcher, the plan's credits, with any its
// complementary slots leave to choose, and Compare, a row with the term and the view, Calendar or
// Course List, then the term's week or list and each slot's card. With ?preview=, the plan shows one
// course in its slot, as the API draws it, with a line saying nothing is saved and End Preview, and a
// preview that fails says why under the plan as it is. With ?compare=, two plans sit side by side in
// panels until Done Comparing, Back or Escape. The header and the term's
// row stay in view as the week scrolls beneath them. The address says which plans and term are open
// (lib/planAddress.ts), so choosing any of them changes it, and what was on screen stays there while
// the next plan arrives. While the sidebar and the assistant are both open, Compare, Done Comparing
// and the view's options show only their icons, each named in a tooltip, as the prototype's do when
// the docked assistant takes their room. Until her set, every plan in it and the plan arrive, loading
// case 01 shows: the term and view render straight away, and the plan's name, credits, Compare and
// week are skeletons, and in compare each panel is, under the bar. Held, as the route table draws it
// while the guard decides on the first load, it reads nothing and shows only its skeleton.
import { keepPreviousData, useQueries, useQuery } from '@tanstack/react-query'
import { type ReactNode, useEffect } from 'react'
import { Link } from 'react-aria-components'
import { useNavigate } from 'react-router'
import { Button } from '@/components/actions/Button/Button.tsx'
import { Card } from '@/components/content/Card/Card.tsx'
import { Arrival } from '@/components/feedback/Arrival/Arrival.tsx'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import { Tooltip } from '@/components/overlays/Tooltip/Tooltip.tsx'
import { ApiError } from '@/lib/api.ts'
import type { components } from '@/lib/api-types.ts'
import { pageNames } from '@/lib/copy.ts'
import { actionLabels, explain } from '@/lib/errors.ts'
import { type PlanAddress, planPath, usePlanAddress } from '@/lib/planAddress.ts'
import { queries } from '@/lib/queryKeys.ts'
import { PlanBar } from './components/PlanBar/PlanBar.tsx'
import { PlanHeaderSkeleton } from './components/PlanBar/PlanHeaderSkeleton.tsx'
import { PlanSwitcher } from './components/PlanSwitcher/PlanSwitcher.tsx'
import { TermView, type View } from './components/TermView/TermView.tsx'
import { creditsOf, creditsWith, endPreview, loadingPreview, previewingLine } from './copy.ts'
import { partnerOf } from './planSet.ts'
import { loadingPlan } from './PlanSkeleton.tsx'
import { coloursOf, weekOf } from './week.ts'
import styles from './PlanView.module.css'

type Plan = components['schemas']['Plan']
type PlanPreview = components['schemas']['PlanPreview']

// What a screen reader hears while the two plans are on their way
const loadingPlans = 'Loading your plans…'

// The course a preview adds, which the API lists among the plan's courses
const previewedCourse = ({ plan, course_code }: PlanPreview) => plan.courses.find((course) => course.code === course_code)

// A plan's credits, and in a preview the course it adds, as "138 credits + 15 with Word Power"
function creditsLine(plan: Plan, previewed: PlanPreview | undefined): string {
  const course = previewed && previewedCourse(previewed)
  if (!course) return creditsOf(plan.credits.total, plan.credits.to_choose)
  return creditsWith(plan.credits.total - course.credits, course.credits, course.name, plan.credits.to_choose)
}

// A preview that failed: why, with Try Again where trying again could help, and End Preview
function previewError(error: unknown, retry: () => void, end: () => void): ReactNode {
  const { title, message, action, reference } = explain(error)
  return (
    <ErrorState variant="region" tone="danger" icon="error" title={title} message={message} reference={reference}>
      {action === 'retry' && (
        <Button variant="secondary" onPress={retry}>
          {actionLabels.retry}
        </Button>
      )}
      <Button variant="quiet" onPress={end}>
        {endPreview}
      </Button>
    </ErrorState>
  )
}

// The view, Calendar or Course List, is the frame's, so it stays as she moves between pages
type PlanViewProps = { iconOnly: boolean; view: View; onViewChange: (view: View) => void; held?: boolean }

export function PlanView({ iconOnly, view, onViewChange, held = false }: PlanViewProps) {
  const address = usePlanAddress()
  const { planId, compareWith, term, preview } = address
  const navigate = useNavigate()
  const setRead = useQuery({ ...queries.plans(), enabled: !held })
  // Held, what the frame's assistant may already have read doesn't count
  const set = held ? undefined : setRead.data
  // Every plan in her set, read once, so each course keeps one colour in all of them
  const setPlans = useQueries({ queries: (set?.plans ?? []).map(({ id }) => queries.plan(id)) })
  // One plan, or two side by side. The read not on screen waits, and keeps what it had for Back.
  const single = useQuery({
    ...queries.plan(planId),
    enabled: compareWith === null && !held,
    placeholderData: keepPreviousData,
  })
  const pair = useQuery({
    ...queries.comparison(planId, compareWith ?? planId),
    enabled: compareWith !== null && !held,
    placeholderData: keepPreviousData,
  })
  // A course previewed in the plan alone. Its id is never used with no preview in the address.
  const previewRead = useQuery({ ...queries.preview(planId, preview ?? ''), enabled: preview !== null && !held })

  // A new plan, a second plan, a term or a preview is a new address. A term replaces the address, so
  // Back skips the terms looked at, and so does ending a preview, which Back would only start again.
  const go = (to: Partial<PlanAddress>, replace = false) => {
    void navigate(planPath({ ...address, ...to }), { replace })
  }

  // Escape leaves compare, as in the prototype, unless something open on the page takes it first, as
  // the plan list does to close
  useEffect(() => {
    if (compareWith === null) return
    const leave = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !event.defaultPrevented) void navigate(planPath({ planId, compareWith: null, term, preview: null }))
    }
    window.addEventListener('keydown', leave)
    return () => window.removeEventListener('keydown', leave)
  }, [compareWith, navigate, planId, term])

  // A plan that was replaced, or an address that isn't one of hers (error case 14)
  const error = compareWith === null ? single.error : pair.error
  if (!held && error instanceof ApiError && error.code === 'plan_not_found') {
    const { title, message } = explain(error)
    return (
      <ErrorState variant="page" icon="calendar_today" title={title} message={message}>
        <Link href="/plan">{actionLabels.go_to_plan}</Link>
      </ErrorState>
    )
  }

  // Her set and every plan in it, by position, once all have arrived, with the plans her lists offer:
  // those her answers kept, and any the assistant has offered since. A plan they hid is in no list.
  const read = setPlans.flatMap(({ data }) => (data ? [data] : []))
  const plans =
    set && read.length === set.plans.length
      ? { set, byPosition: read.sort((a, b) => a.position - b.position), shown: set.plans.filter((summary) => !summary.hidden) }
      : undefined
  // Whether a read the view waits for is still on its way. Held, they all are.
  const setWaiting = held || setRead.isPending || setPlans.some(({ isPending }) => isPending)

  const bar = (header: ReactNode) => (
    <PlanBar
      term={term}
      onTermChange={(chosen) => go({ term: chosen }, true)}
      view={view}
      onViewChange={onViewChange}
      iconOnly={iconOnly}
    >
      {header}
    </PlanBar>
  )

  if (compareWith === null) {
    const plan = held ? undefined : single.data
    // In a preview, the plan as the preview draws it, once it has arrived. A preview that failed leaves
    // the plan as it is.
    const previewFailed = preview !== null && previewRead.isError
    const previewed = preview === null || held ? undefined : previewRead.data
    const drawn = preview === null || previewFailed ? plan : previewed?.plan
    const open = plans && drawn ? { ...plans, plan: drawn, partner: partnerOf(plans.set.plans, drawn), previewed } : undefined
    const waiting = setWaiting || single.isPending || (preview !== null && previewRead.isPending)
    return (
      <>
        {bar(
          <>
            <h1 className="visually-hidden">{pageNames.plan}</h1>
            <Arrival data={open} waiting={waiting} skeleton={<PlanHeaderSkeleton />}>
              {({ plan, shown, partner, previewed }) => {
                // A plan from an earlier set, or one her answers hid, opened from a link or her history,
                // isn't one to switch between, so it shows its name alone
                const switchable = shown.length > 1 && shown.some((summary) => summary.id === plan.id)
                return (
                  <>
                    {switchable ? (
                      <PlanSwitcher
                        label="Plan"
                        variant="outlined"
                        plans={shown}
                        selected={plan.id}
                        onChange={(chosen) => go({ planId: chosen, preview: null })}
                      />
                    ) : (
                      <p className={styles.name}>{plan.name}</p>
                    )}
                    <p className={styles.credits}>{creditsLine(plan, previewed)}</p>
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
                  </>
                )
              }}
            </Arrival>
          </>,
        )}
        <Arrival
          key="single"
          data={open}
          waiting={waiting}
          skeleton={<TermView plan={null} view={view} />}
          status={preview === null ? loadingPlan : loadingPreview}
        >
          {({ plan, byPosition, previewed }) => {
            const course = previewed && previewedCourse(previewed)
            const marks = previewed && { code: previewed.course_code, forced: previewed.forced }
            return (
              <>
                {course && (
                  <div className={styles.previewing}>
                    <p className={styles.previewLine}>{previewingLine(course.name)}</p>
                    <Button variant="secondary" onPress={() => go({ preview: null }, true)}>
                      {endPreview}
                    </Button>
                  </div>
                )}
                {previewFailed && previewError(previewRead.error, () => void previewRead.refetch(), () => go({ preview: null }, true))}
                <TermView
                  plan={plan}
                  term={term}
                  view={view}
                  week={weekOf(plan, term, marks)}
                  colours={coloursOf([...byPosition, plan])}
                  previewed={previewed?.course_code}
                />
              </>
            )
          }}
        </Arrival>
      </>
    )
  }

  const comparison = held ? undefined : pair.data
  const compared = plans && comparison ? { ...plans, comparison } : undefined
  return (
    <>
      {bar(
        <>
          <h1 className={styles.title}>Comparing Plans</h1>
          <Tooltip text="Done Comparing" isDisabled={!iconOnly}>
            <Button variant="secondary" icon="close" iconOnly={iconOnly} onPress={() => go({ compareWith: null })}>
              Done Comparing
            </Button>
          </Tooltip>
        </>,
      )}
      <Arrival
        key="compare"
        data={compared}
        waiting={setWaiting || pair.isPending}
        // Each panel's name over its week, as case 01 draws a plan
        skeleton={
          <div aria-hidden="true" className={styles.panels}>
            {[0, 1].map((panel) => (
              <Card
                key={panel}
                title={<Skeleton variant="line" length={24} />}
                level={2}
                meta={
                  <p className={styles.panelCredits}>
                    <Skeleton variant="line" length={11} />
                  </p>
                }
              >
                <TermView plan={null} view={view} compact />
              </Card>
            ))}
          </div>
        }
        status={loadingPlans}
      >
        {({ byPosition, shown, comparison: { first, second } }) => {
          const colours = coloursOf([...byPosition, first, second])
          // Another plan to swap in for the second, when the set has one beyond these two
          const swappable = shown.some((summary) => summary.id !== first.id && summary.id !== second.id)
          return (
            <div className={styles.panels}>
              <Card
                title={first.name}
                level={2}
                meta={<p className={styles.panelCredits}>{creditsOf(first.credits.total, first.credits.to_choose)}</p>}
              >
                <TermView plan={first} term={term} view={view} week={weekOf(first, term)} colours={colours} compact />
              </Card>
              <Card
                title={second.name}
                level={2}
                meta={<p className={styles.panelCredits}>{creditsOf(second.credits.total, second.credits.to_choose)}</p>}
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
                <TermView plan={second} term={term} view={view} week={weekOf(second, term)} colours={colours} compact />
              </Card>
            </div>
          )
        }}
      </Arrival>
    </>
  )
}
