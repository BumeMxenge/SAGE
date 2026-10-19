// One year of the review: its courses in a table, in the order the prototype lists them, by term and
// then by code. Course names show exactly as the transcript prints them. A line the reading partly
// guessed says "Check" beside its outcome, so the warning never rests on colour alone. In edit mode
// each outcome is a Select of UCT's result symbols, and each course can be removed.
import { IconButton } from '@/components/actions/IconButton/IconButton.tsx'
import { DataTable } from '@/components/content/DataTable/DataTable.tsx'
import { Select } from '@/components/inputs/Select/Select.tsx'
import { SelectItem } from '@/components/inputs/Select/SelectItem.tsx'
import type { ReviewLine } from '@/features/onboarding/review.ts'
import type { components } from '@/lib/api-types.ts'
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
  // UCT's result symbols, from the catalogue, with each one's words
  symbols: components['schemas']['ResultSymbol'][]
  editing: boolean
  onChangeOutcome: (line: ReviewLine, result: string) => void
  onRemove: (line: ReviewLine) => void
}

export function YearTable({ caption, lines, symbols, editing, onChangeOutcome, onRemove }: YearTableProps) {
  const words = new Map(symbols.map((symbol) => [symbol.symbol, symbol.label]))
  const ordered = lines.toSorted(
    (first, second) =>
      termOrder.indexOf(first.term) - termOrder.indexOf(second.term) || first.course_code.localeCompare(second.course_code),
  )
  return (
    <DataTable
      caption={caption}
      columns={editing ? [...columns, { key: 'remove', header: 'Remove' }] : columns}
      rows={ordered.map((line) => ({
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
                  selectedKey={line.result}
                  onSelectionChange={(result) => {
                    if (result !== null && result !== line.result) onChangeOutcome(line, String(result))
                  }}
                >
                  {symbols.map((symbol) => (
                    <SelectItem key={symbol.symbol} id={symbol.symbol} description={symbol.symbol}>
                      {symbol.label}
                    </SelectItem>
                  ))}
                </Select>
              ) : (
                (words.get(line.result) ?? line.result)
              )}
              {line.unverified && <span className={styles.check}>Check</span>}
            </span>
          ),
          remove: <IconButton label={`Remove ${line.course_code}`} icon="close" onPress={() => onRemove(line)} />,
        },
      }))}
    />
  )
}
