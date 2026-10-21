// A plan's week in one term: Monday to Friday across the top, the hours down the side, and each
// meeting a block in its course's colour, as tall as the meeting is long. The days and hours are for
// the eye. To a screen reader each day is a list named by the day, and each block says its course,
// its times and any options it stands for. The course list is the plain equivalent of the whole week.
// Compact is the smaller week inside a compare panel, whose blocks leave the times to the hours beside
// them.
import type { CourseColour, Week } from '../../week.ts'
import styles from './Timetable.module.css'

const days = [
  { day: 1, short: 'Mon', long: 'Monday' },
  { day: 2, short: 'Tue', long: 'Tuesday' },
  { day: 3, short: 'Wed', long: 'Wednesday' },
  { day: 4, short: 'Thu', long: 'Thursday' },
  { day: 5, short: 'Fri', long: 'Friday' },
]

const clock = (hour: number) => `${String(hour).padStart(2, '0')}:00`

type TimetableProps = {
  week: Week
  colours: ReadonlyMap<string, CourseColour>
  compact?: boolean
}

export function Timetable({ week, colours, compact = false }: TimetableProps) {
  const hours = Array.from({ length: week.hours }, (_, index) => week.firstHour + index)
  return (
    <div className={styles.timetable} data-compact={compact || undefined} style={{ '--hours': week.hours }}>
      {days.map(({ day, short }) => (
        <span key={day} aria-hidden="true" className={styles.dayLabel}>
          {short}
        </span>
      ))}
      <div aria-hidden="true" className={styles.hours}>
        {hours.map((hour) => (
          <span key={hour}>{clock(hour)}</span>
        ))}
      </div>
      {days.map(({ day, long }) => (
        <ul key={day} aria-label={long} className={styles.day}>
          {week.blocks
            .filter((block) => block.day === day)
            .map((block) => (
              <li
                key={block.key}
                className={styles.block}
                data-colour={colours.get(block.code)}
                style={{ '--start': block.start, '--length': block.length, '--lane': block.lane, '--lanes': block.lanes }}
              >
                <p className={styles.code}>
                  {block.code}
                  <span className="visually-hidden"> {block.name}</span>
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
      ))}
    </div>
  )
}
