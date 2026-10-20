// Course History: the courses on the record the student confirmed at onboarding, a table for each
// year, newest first, with each year's average and credits and the average across them all. The API
// works out every figure, and the page shows each average to one decimal, as the record does. The
// title and the cumulative average stay at the top of the window while the tables scroll beneath.
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

// One decimal, rounded half up from the API's two. The formatter rounds the decimal digits, not the
// computer's binary copy of them, so 63.15, held as 63.1499…, shows as 63.2%.
const oneDecimal = new Intl.NumberFormat('en-GB', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const percent = (average: number) => `${oneDecimal.format(average)}%`

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
    <>
      <PageHeader
        title={pageNames.history}
        sticky
        figure={
          cumulative !== null && (
            <p className={styles.cumulative}>
              Cumulative Average: <span className={styles.value}>{percent(cumulative)}</span>
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
    </>
  )
}
