// One year of the review: its courses in a table, in the order the prototype lists them, by term and
// then by code. Course names show exactly as the transcript prints them. A line the reading partly
// guessed says "Check" beside its outcome, so the warning never rests on colour alone.
import { DataTable } from '@/components/content/DataTable/DataTable.tsx'
import type { ReviewLine } from '@/features/onboarding/review.ts'
import { termLabels } from '@/lib/copy.ts'
import styles from './YearTable.module.css'

// The semester's quarters and its winter term follow it; full-year courses come after both semesters
const termOrder: ReviewLine['term'][] = ['sem1', 'q1', 'q2', 'winter', 'sem2', 'q3', 'q4', 'full_year', 'summer', 'other']

const columns = [
  { key: 'course', header: 'Course' },
  { key: 'term', header: 'Term' },
  { key: 'credits', header: 'Credits' },
  { key: 'outcome', header: 'Outcome' },
]

type YearTableProps = {
  caption: string
  lines: ReviewLine[]
  // Each result symbol's words, from the catalogue
  outcomes: Map<string, string>
}

export function YearTable({ caption, lines, outcomes }: YearTableProps) {
  const ordered = lines.toSorted(
    (first, second) =>
      termOrder.indexOf(first.term) - termOrder.indexOf(second.term) || first.course_code.localeCompare(second.course_code),
  )
  return (
    <DataTable
      caption={caption}
      columns={columns}
      rows={ordered.map((line) => ({
        id: line.id,
        cells: {
          course: `${line.course_code}: ${line.course_name}`,
          term: termLabels[line.term],
          credits: line.credits,
          outcome: (
            <>
              {outcomes.get(line.result) ?? line.result}
              {line.unverified && <span className={styles.check}>Check</span>}
            </>
          ),
        },
      }))}
    />
  )
}
