// One plan's term, as its week or its list, alone or in a compare panel. A term with no courses says
// so. Under the week, a line names what it can't draw. The plan's complementary studies cards will sit
// below both, in the same column.
import { EmptyState } from '@/components/feedback/EmptyState/EmptyState.tsx'
import type { components } from '@/lib/api-types.ts'
import type { PlanTerm } from '@/lib/planAddress.ts'
import { type CourseColour, termCourses, type Week } from '../../week.ts'
import { CourseList } from '../CourseList/CourseList.tsx'
import { Timetable } from '../Timetable/Timetable.tsx'
import styles from './TermView.module.css'

type Plan = components['schemas']['Plan']

export type View = 'calendar' | 'list'

type TermViewProps = {
  plan: Plan
  term: PlanTerm
  view: View
  week: Week
  colours: ReadonlyMap<string, CourseColour>
  // The codes only this plan has, when it's compared with another
  only: ReadonlySet<string>
  compact?: boolean
}

export function TermView({ plan, term, view, week, colours, only, compact = false }: TermViewProps) {
  const courses = termCourses(plan, term)
  if (courses.length === 0) {
    return (
      <EmptyState
        icon={view === 'calendar' ? 'calendar_today' : 'format_list_bulleted'}
        title="No Courses This Term"
        message="Choose another term to see this plan's courses."
      />
    )
  }
  return (
    <div className={styles.termView}>
      {view === 'list' ? (
        <CourseList courses={courses} only={only} />
      ) : (
        <>
          <Timetable week={week} colours={colours} only={only} compact={compact} />
          {week.noSetTimes && <p className={styles.noSetTimes}>{week.noSetTimes}</p>}
        </>
      )}
    </div>
  )
}
