// One year of the review: its courses in a table, in the order the prototype lists them, by term and
// then by code. Course names show exactly as the transcript prints them, and each outcome in a word,
// such as Passed. A line the reading partly guessed says "Check" beside its outcome, so the warning
// never rests on colour alone. In edit mode each outcome is a plain Select of the outcomes a student
// sets, and the line's own where it is another, and each course can be removed. The table fills the
// height it is given and scrolls its rows inside.
import type { Ref } from 'react'
import { IconButton } from '@/components/actions/IconButton/IconButton.tsx'
import { DataTable } from '@/components/content/DataTable/DataTable.tsx'
import { Select } from '@/components/inputs/Select/Select.tsx'
import { SelectItem } from '@/components/inputs/Select/SelectItem.tsx'
import { isOutcome, type Outcome, offeredOutcomes, outcomes, type ReviewLine, wordFor } from '@/features/onboarding/review.ts'
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
  // Each result symbol's outcome, from the catalogue
  outcomeOf: Map<string, Outcome>
  editing: boolean
  onChangeOutcome: (line: ReviewLine, outcome: Outcome) => void
  onRemove: (line: ReviewLine) => void
  // The table's scroll box, so the review can move focus to it as each year opens
  ref?: Ref<HTMLElement>
}

export function YearTable({ caption, lines, outcomeOf, editing, onChangeOutcome, onRemove, ref }: YearTableProps) {
  const ordered = lines.toSorted(
    (first, second) =>
      termOrder.indexOf(first.term) - termOrder.indexOf(second.term) || first.course_code.localeCompare(second.course_code),
  )
  return (
    <DataTable
      ref={ref}
      scrollable
      caption={caption}
      columns={editing ? [...columns, { key: 'remove', header: 'Remove' }] : columns}
      rows={ordered.map((line) => {
        const current = outcomeOf.get(line.result)
        // A line printed with an outcome the review doesn't offer keeps it in its own list
        const choices = current && !offeredOutcomes.includes(current) ? [...offeredOutcomes, current] : offeredOutcomes
        return {
          id: line.id,
          cells: {
            course: `${line.course_code}: ${line.course_name}`,
            term: termLabels[line.term],
            credits: line.credits,
            outcome: (
              <span className={styles.outcome}>
                {editing ? (
                  <Select
                    variant="plain"
                    label={`Outcome for ${line.course_code}`}
                    selectedKey={current ?? null}
                    onSelectionChange={(outcome) => {
                      if (isOutcome(outcome) && outcome !== current) onChangeOutcome(line, outcome)
                    }}
                  >
                    {choices.map((outcome) => (
                      <SelectItem key={outcome} id={outcome}>
                        {outcomes[outcome].word}
                      </SelectItem>
                    ))}
                  </Select>
                ) : (
                  wordFor(line.result, outcomeOf)
                )}
                {line.unverified && <span className={styles.check}>Check</span>}
              </span>
            ),
            remove: <IconButton label={`Remove ${line.course_code}`} icon="close" onPress={() => onRemove(line)} />,
          },
        }
      })}
    />
  )
}
