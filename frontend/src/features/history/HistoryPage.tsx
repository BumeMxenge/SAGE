// Course History: the courses on the record the student confirmed at onboarding, a table for each
// year, newest first, with each year's average and credits and the average across them all. The API
// works out every figure, and the page shows each average to one decimal, as the record does. The
// title and the cumulative average stay at the top of the window while the tables scroll beneath.
// Until the record arrives, loading case 05 shows: the title and the average's label render straight
// away, and the average, a year's heading and its rows are skeletons. Held, as the route table draws
// it while the guard decides on the first load, it reads nothing and shows only its skeleton.
import { useQuery } from '@tanstack/react-query'
import { DataTable, type DataTableColumn } from '@/components/content/DataTable/DataTable.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { Arrival } from '@/components/feedback/Arrival/Arrival.tsx'
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
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

// The skeleton's year: each course name's length in characters, as loading case 05 varies them
const waitingNames = [26, 34, 22, 30, 18, 28, 24]

const yearSkeleton = (
  <div aria-hidden="true" className={styles.years}>
    <DataTable
      outlined
      caption={<Skeleton variant="line" length={14} />}
      detail={<Skeleton variant="line" length={20} />}
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
          result: (
            <span className={styles.result}>
              <Skeleton variant="line" length={2} />
            </span>
          ),
        },
      }))}
    />
  </div>
)

export function HistoryPage({ held = false }: { held?: boolean }) {
  const read = useQuery({ ...queries.history(), enabled: !held })
  const history = held ? undefined : read.data
  const waiting = held || read.isPending
  // A record with no marks has no cumulative average, so its figure goes once the record says so
  const cumulative = history?.cumulative_average
  return (
    <div className={styles.page}>
      <PageHeader
        title={pageNames.history}
        sticky
        figure={
          cumulative !== null &&
          (waiting || cumulative !== undefined) && (
            <p className={styles.cumulative}>
              Cumulative Average:{' '}
              <Arrival data={cumulative} waiting={waiting} skeleton={<Skeleton variant="line" length={5} />}>
                {(average) => <span className={styles.value}>{percent(average)}</span>}
              </Arrival>
            </p>
          )
        }
      />
      <Arrival data={history} waiting={waiting} skeleton={yearSkeleton} status="Loading your course history…">
        {({ years }) => (
          <div className={styles.years}>
            {years.map((year) => (
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
        )}
      </Arrival>
    </div>
  )
}
