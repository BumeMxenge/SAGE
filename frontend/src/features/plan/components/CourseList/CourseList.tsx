// A plan's courses in one term, a table for each list the handbook puts them on, such as Fourth Year
// Core Courses (ME), with the list's credits that term. A course that runs for one quarter of its
// semester is marked so. While the plan is on its way, one table of skeleton rows stands in for them,
// hidden from screen readers, under the real column headers.
import { DataTable, type DataTableColumn } from '@/components/content/DataTable/DataTable.tsx'
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import type { components } from '@/lib/api-types.ts'
import { quarterOf } from '../../week.ts'
import styles from './CourseList.module.css'

type PlanCourse = components['schemas']['PlanCourse']

const columns: DataTableColumn[] = [
  { key: 'code', header: 'Code', fit: true },
  { key: 'course', header: 'Course' },
  { key: 'credits', header: 'Credits', align: 'end', fit: true },
]

type Group = { key: string; label: string; courses: PlanCourse[] }

// Each course goes on its first list. The lists follow their keys, which put earlier years first and
// core before elective groups; a course on none of her curriculum's lists comes last.
function groupsOf(courses: PlanCourse[]): Group[] {
  const lists = new Map<string, Group>()
  const others: PlanCourse[] = []
  for (const course of courses) {
    const list = course.groups.at(0)
    if (!list) {
      others.push(course)
      continue
    }
    const group = lists.get(list.key) ?? { key: list.key, label: list.label, courses: [] }
    group.courses.push(course)
    lists.set(list.key, group)
  }
  const sorted = [...lists.values()].sort((a, b) => a.key.localeCompare(b.key))
  return others.length > 0 ? [...sorted, { key: 'other', label: 'Other Courses', courses: others }] : sorted
}

// The skeleton's rows, each course name's length in characters
const waitingNames = [30, 24, 34, 28]

// null while the plan is on its way
export function CourseList({ courses }: { courses: PlanCourse[] | null }) {
  if (courses === null) {
    return (
      <div aria-hidden="true" className={styles.courseList}>
        <DataTable
          outlined
          caption={<Skeleton variant="line" length={26} />}
          detail={<Skeleton variant="line" length={10} />}
          columns={columns}
          rows={waitingNames.map((length) => ({
            id: String(length),
            cells: {
              code: (
                <span className={styles.code}>
                  <Skeleton variant="line" length={8} />
                </span>
              ),
              course: <Skeleton variant="line" length={length} />,
              credits: (
                <span className={styles.credits}>
                  <Skeleton variant="line" length={2} />
                </span>
              ),
            },
          }))}
        />
      </div>
    )
  }
  return (
    <div className={styles.courseList}>
      {groupsOf(courses).map((group) => (
        <DataTable
          key={group.key}
          outlined
          caption={group.label}
          detail={`${group.courses.reduce((total, course) => total + course.credits, 0)} credits`}
          columns={columns}
          rows={group.courses.map((course) => {
            const quarter = quarterOf(course.term)
            return {
              id: course.code,
              cells: {
                code: <span className={styles.code}>{course.code}</span>,
                course: (
                  <>
                    {course.name}
                    {quarter && <span className={styles.mark}> {quarter}</span>}
                  </>
                ),
                credits: <span className={styles.credits}>{course.credits}</span>,
              },
            }
          })}
        />
      ))}
    </div>
  )
}
