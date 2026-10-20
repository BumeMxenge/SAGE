// Course History: the courses on the record the student confirmed at onboarding, a table for each
// year, newest first, with each year's average and credits and the average across them all. The API
// works out every figure, and the page shows each average as a whole percent, as the prototype does.
import { useQuery } from '@tanstack/react-query'
import { DataTable, type DataTableColumn } from '@/components/content/DataTable/DataTable.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { pageNames } from '@/lib/copy.ts'
import { queries } from '@/lib/queryKeys.ts'
import styles from './HistoryPage.module.css'

// The year of study in words, as the prototype names each year, and past the tenth its number
const ordinals = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth']

function yearOfStudy(year: number): string {
  const word: string | undefined = ordinals[year - 1]
  return word ? `${word} Year` : `Year ${year}`
}

// A whole percent, rounded half up as the backend rounds, so 72.5 shows as 73%
const percent = (average: number) => `${Math.round(average)}%`

// Result is the transcript's heading for the column that holds a mark, or a symbol where there is none
const columns: DataTableColumn[] = [
  { key: 'code', header: 'Code', fit: true },
  { key: 'course', header: 'Course' },
  { key: 'result', header: 'Result', align: 'end', fit: true },
]

export function HistoryPage() {
  const { data: history } = useQuery(queries.history())
  // Nothing shows until the record arrives. Its skeleton comes with the app's other loading states.
  if (!history) return null
  const cumulative = history.cumulative_average
  return (
    <div className={styles.page}>
      <PageHeader
        title={pageNames.history}
        figure={
          cumulative !== null && (
            <p className={styles.cumulative}>
              <span className={styles.value}>{percent(cumulative)}</span>{' '}
              <span className={styles.label}>Cumulative Average</span>
            </p>
          )
        }
      />
      <div className={styles.years}>
        {history.years.map((year) => (
          <DataTable
            key={year.academic_year}
            outlined
            caption={`${year.academic_year} · ${yearOfStudy(year.year_of_study)}`}
            detail={
              <>
                {year.average !== null && <span className={styles.average}>Average {percent(year.average)}</span>}{' '}
                <span>{year.credits} credits</span>
              </>
            }
            columns={columns}
            // A course appears once a term in a year, so its term and code name its row
            rows={year.lines.map((line) => ({
              id: `${line.term}-${line.code}`,
              cells: {
                code: <span className={styles.code}>{line.code}</span>,
                course: line.name,
                result: <span className={styles.result}>{line.mark ?? line.result}</span>,
              },
            }))}
          />
        ))}
      </div>
    </div>
  )
}
