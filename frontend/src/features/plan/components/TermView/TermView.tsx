// One plan's term, as its week or its list, alone or in a compare panel. A term with no courses says
// so, under the panel's title in compare. Under the week, a line names what it can't draw. While the
// plan is on its way, the week's or the list's skeleton takes its place. The plan's complementary
// studies cards will sit below both, in the same column.
import { EmptyState } from '@/components/feedback/EmptyState/EmptyState.tsx'
import type { components } from '@/lib/api-types.ts'
import type { PlanTerm } from '@/lib/planAddress.ts'
import { type CourseColour, termCourses, type Week } from '../../week.ts'
import { CourseList } from '../CourseList/CourseList.tsx'
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
  if (courses.length === 0) {
    return (
      <EmptyState
        level={compact ? 3 : 2}
        icon={view === 'calendar' ? 'calendar_today' : 'format_list_bulleted'}
        title="No Courses This Term"
        message="Choose another term to see this plan's courses."
      />
    )
  }
  return (
    <div className={styles.termView}>
      {view === 'list' ? (
        <CourseList courses={courses} />
      ) : (
        <>
          <Timetable week={week} colours={colours} compact={compact} />
          {week.noSetTimes && <p className={styles.noSetTimes}>{week.noSetTimes}</p>}
        </>
      )}
    </div>
  )
}
