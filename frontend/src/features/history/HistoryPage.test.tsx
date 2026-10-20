// Course History shows the API's record as the prototype does: each year named by its year of study,
// each average a whole percent rounded half up, a mark or an average of 0 as 0, the symbol of a course
// with no mark, and no average where there is none. The records are made up, and their figures stand
// in for the API's own sums, so they needn't add up.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { queries } from '@/lib/queryKeys.ts'
import { HistoryPage } from './HistoryPage.tsx'

type History = components['schemas']['History']
type HistoryYear = components['schemas']['HistoryYear']
type HistoryLine = components['schemas']['HistoryLine']

afterEach(cleanup)

// The record is already read, so nothing goes to the network
function show(history: History) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
  queryClient.setQueryData(queries.history().queryKey, history)
  render(
    <QueryClientProvider client={queryClient}>
      <HistoryPage />
    </QueryClientProvider>,
  )
}

// A made-up 16-credit course in the first semester
function course(code: string, name: string, result: string, mark: number | null): HistoryLine {
  return { code, name, term: 'sem1', credits: 16, nqf_level: 7, result, mark }
}

function year(academic_year: number, year_of_study: number, average: number | null, lines: HistoryLine[]): HistoryYear {
  return { academic_year, year_of_study, credits: 16 * lines.length, average, lines }
}

const project = course('EEE4022S', 'Made-up Research Project', 'OS', null)

// Half up, as the backend rounds: 72.5 is 73%, where rounding a half to the even number would give 72%,
// and 72.49 is 72%
it('names each year by its year of study, and rounds averages to a whole percent, half up', () => {
  show({ cumulative_average: 72.5, years: [year(2025, 3, 72.49, [course('EEE3096S', 'Made-up Embedded Systems', '2+', 72)])] })
  expect(screen.getByText('73%')).toBeTruthy()
  expect(screen.getByRole('table', { name: '2025 · Third Year Average 72% 16 credits' })).toBeTruthy()
})

it('shows a mark or an average of 0, and the symbol of a course with no mark', () => {
  show({
    cumulative_average: 0,
    years: [year(2024, 2, 0, [course('MEC2045S', 'Made-up Mechanics', 'F', 0), course('EEE1000X', 'Made-up Practical Training', 'GIP', null)])],
  })
  expect(screen.getByText('0%')).toBeTruthy()
  const table = screen.getByRole('table', { name: '2024 · Second Year Average 0% 32 credits' })
  const cells = within(table)
    .getAllByRole('cell')
    .map((cell) => cell.textContent)
  expect(cells).toEqual(['MEC2045S', 'Made-up Mechanics', '0', 'EEE1000X', 'Made-up Practical Training', 'GIP'])
})

// An average of 0% would tell a student they failed everything, when nothing has a mark yet
it('shows no average where no course has a mark yet', () => {
  show({ cumulative_average: null, years: [year(2026, 1, null, [project])] })
  expect(screen.queryByText('Cumulative Average')).toBeNull()
  expect(screen.getByRole('table', { name: '2026 · First Year 16 credits' })).toBeTruthy()
})

// The words run out after the tenth year, so the eleventh goes by its number
it('names a year past the tenth by its number', () => {
  show({ cumulative_average: null, years: [year(2036, 11, null, [project]), year(2035, 10, null, [project])] })
  expect(screen.getByRole('table', { name: '2036 · Year 11 16 credits' })).toBeTruthy()
  expect(screen.getByRole('table', { name: '2035 · Tenth Year 16 credits' })).toBeTruthy()
})
