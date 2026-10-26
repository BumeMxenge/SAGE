// A plan's week in one term: Monday to Friday across the top, the hours down the side, and each
// meeting a block in its course's colour, as tall as the meeting is long. The days and hours are for
// the eye. To a screen reader each day is a list named by the day, and each block says its course,
// its times and any options it stands for. A preview's course is dashed inside its edge, and says so to
// a screen reader. The course list is the plain equivalent of the whole week.
// Compact is the smaller week inside a compare panel, whose blocks leave the times to the hours beside
// them. While the plan is on its way it draws the shortest week, its days and hours, with skeleton
// meetings where loading case 01 draws them.
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import { inThisPreview } from '../../copy.ts'
import { type CourseColour, shortestWeek, type Week } from '../../week.ts'
import styles from './Timetable.module.css'

const days = [
  { day: 1, short: 'Mon', long: 'Monday' },
  { day: 2, short: 'Tue', long: 'Tuesday' },
  { day: 3, short: 'Wed', long: 'Wednesday' },
  { day: 4, short: 'Thu', long: 'Thursday' },
  { day: 5, short: 'Fri', long: 'Friday' },
]

// The hours the skeleton's meetings start, each day, each an hour long, as loading case 01 places them
const waitingStarts: Record<number, number[]> = { 1: [8, 10, 12], 2: [8, 10, 12], 3: [8, 10, 12, 14], 4: [10, 12], 5: [8, 10, 12, 14] }
const waitingLength = 60

const clock = (hour: number) => `${String(hour).padStart(2, '0')}:00`

type TimetableProps = { compact?: boolean } & (
  | { week: Week; colours: ReadonlyMap<string, CourseColour> }
  // The plan is on its way
  | { week: null }
)

export function Timetable(props: TimetableProps) {
  const { firstHour, hours } = props.week ?? shortestWeek
  const compact = props.compact ?? false
  return (
    <div className={styles.timetable} data-compact={compact || undefined} style={{ '--hours': hours }}>
      {days.map(({ day, short }) => (
        <span key={day} aria-hidden="true" className={styles.dayLabel}>
          {short}
        </span>
      ))}
      <div aria-hidden="true" className={styles.hours}>
        {Array.from({ length: hours }, (_, index) => firstHour + index).map((hour) => (
          <span key={hour}>{clock(hour)}</span>
        ))}
      </div>
      {days.map(({ day, long }) => {
        if (props.week === null) {
          return (
            <div key={day} className={styles.day}>
              {waitingStarts[day].map((hour) => (
                <span
                  key={hour}
                  className={styles.waiting}
                  style={{ '--start': (hour - firstHour) * 60, '--length': waitingLength }}
                >
                  <Skeleton variant="block" />
                </span>
              ))}
            </div>
          )
        }
        const { colours } = props
        return (
          <ul key={day} aria-label={long} className={styles.day}>
            {props.week.blocks
              .filter((block) => block.day === day)
              .map((block) => (
                <li
                  key={block.key}
                  className={styles.block}
                  data-colour={colours.get(block.code)}
                  data-previewed={block.previewed || undefined}
                  style={{ '--start': block.start, '--length': block.length, '--lane': block.lane, '--lanes': block.lanes }}
                >
                  <p className={styles.code}>
                    {block.code}
                    <span className="visually-hidden">
                      {' '}
                      {block.name}
                      {block.previewed && `, ${inThisPreview}`}
                    </span>
                  </p>
                  <p className={styles.detail}>
                    {block.quarter}
                    <span aria-hidden="true" className={styles.times}>
                      {block.quarter && ' · '}
                      {block.from}–{block.to}
                    </span>
                    <span className="visually-hidden">
                      {' '}
                      {block.from} to {block.to}
                    </span>
                  </p>
                  {block.options && <p className={styles.detail}>{block.options}</p>}
                </li>
              ))}
          </ul>
        )
      })}
    </div>
  )
}
