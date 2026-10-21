// A plan's courses in one term, a table for each list the handbook puts them on, such as Fourth Year
// Core Courses (ME), with the list's credits that term. A course that runs for one quarter of its
// semester is marked so, and when two plans are compared, so is a course only this one has.
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import { DataTable, type DataTableColumn } from '@/components/content/DataTable/DataTable.tsx'
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

type CourseListProps = {
  courses: PlanCourse[]
  // The codes only this plan has, when it's compared with another
  only: ReadonlySet<string>
}

export function CourseList({ courses, only }: CourseListProps) {
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
                    {only.has(course.code) && (
                      <span className={styles.only}>
                        <Icon name="difference" />
                        Only in this plan
                      </span>
                    )}
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
