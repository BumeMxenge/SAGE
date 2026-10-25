// One plan's term, as its week or its list, alone or in a compare panel. A term with no courses says
// so, under the panel's title in compare. Under the week, a line names what it can't draw. Under the
// week or the list, in the same column, each of the plan's complementary slots has its card, in every
// term, as a slot is the year's. While the plan is on its way, the week's or the list's skeleton takes
// its place.
import type { ReactNode } from 'react'
import { EmptyState } from '@/components/feedback/EmptyState/EmptyState.tsx'
import type { components } from '@/lib/api-types.ts'
import type { PlanTerm } from '@/lib/planAddress.ts'
import { type CourseColour, termCourses, type Week } from '../../week.ts'
import { CourseList } from '../CourseList/CourseList.tsx'
import { SlotCard } from '../SlotCard/SlotCard.tsx'
import { Timetable } from '../Timetable/Timetable.tsx'
import styles from './TermView.module.css'

type Plan = components['schemas']['Plan']

export type View = 'calendar' | 'list'

type TermViewProps = { view: View; compact?: boolean } & (
  | { plan: Plan; term: PlanTerm; week: Week; colours: ReadonlyMap<string, CourseColour> }
  // The plan is on its way
  | { plan: null }
)

export function TermView(props: TermViewProps) {
  const { view, compact = false } = props
  if (props.plan === null) {
    return (
      <div className={styles.termView}>
        {view === 'list' ? <CourseList courses={null} /> : <Timetable week={null} compact={compact} />}
      </div>
    )
  }
  const { plan, term, week, colours } = props
  const courses = termCourses(plan, term)
  let content: ReactNode
  if (courses.length === 0) {
    content = (
      <EmptyState
        level={compact ? 3 : 2}
        icon={view === 'calendar' ? 'calendar_today' : 'format_list_bulleted'}
        title="No Courses This Term"
        message="Choose another term to see this plan's courses."
      />
    )
  } else if (view === 'list') {
    content = <CourseList courses={courses} />
  } else {
    content = (
      <>
        <Timetable week={week} colours={colours} compact={compact} />
        {week.noSetTimes && <p className={styles.noSetTimes}>{week.noSetTimes}</p>}
      </>
    )
  }
  return (
    <div className={styles.termView}>
      {content}
      {plan.slots.map((slot, index) => (
        <SlotCard key={index} slot={slot} planId={plan.id} level={compact ? 3 : 2} />
      ))}
    </div>
  )
}
