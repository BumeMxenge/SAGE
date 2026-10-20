// Finish Setup waits for the student to confirm their last year: disabled before the box is ticked,
// saying so beside it, enabled once it is, and disabled again when it is unticked. And the review
// leaves out the note that results are pending, by its code, as each such course already says In
// progress.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { queries } from '@/lib/queryKeys.ts'
import { ReviewStep } from './ReviewStep.tsx'

// A made-up record of one year, so its first year is its last, naming one programme
const transcript: components['schemas']['Transcript'] = {
  student_number: 'QRTILV999',
  programme: 'Made-up Programme',
  curriculum_options: [{ code: 'MADE01', name: 'Made-up Programme 4-year curriculum' }],
  issued_on: null,
  lines: [
    {
      academic_year: 2025,
      term: 'sem1',
      course_code: 'EEE3088F',
      course_name: 'Design Principles',
      credits: 16,
      nqf_level: 7,
      result: '1',
      mark: 80,
      unverified: false,
    },
  ],
  warnings: [],
}

const catalogue: components['schemas']['Catalogue'] = {
  year: 2026,
  curricula: [{ code: 'MADE01', name: 'Made-up Programme 4-year curriculum' }],
  courses: [],
  symbols: [{ symbol: '1', outcome: 'pass', label: 'First class (75 to 100%)' }],
}

beforeEach(() => {
  // Each year opens at the top of the page, which jsdom can't scroll. Nor does it measure sizes, so a
  // year's table has nothing to scroll and counts as read at once.
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      disconnect() {}
    },
  )
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

// The catalogue is already read, so nothing goes to the network
function review(record: components['schemas']['Transcript']) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
  queryClient.setQueryData(queries.catalogue().queryKey, catalogue)
  render(
    <QueryClientProvider client={queryClient}>
      <ReviewStep transcript={record} curriculum="MADE01" onSaved={async () => {}} />
    </QueryClientProvider>,
  )
}

it('keeps Finish Setup disabled until the last year is confirmed', () => {
  review(transcript)
  const finish = screen.getByRole('button', { name: 'Finish Setup' })
  const confirmation = screen.getByRole('checkbox', { name: 'This reflects my current academic record' })

  const hint = 'Tick the box above to finish.'

  expect(finish).toHaveProperty('disabled', true)
  expect(screen.getByText(hint)).toBeTruthy()
  fireEvent.click(confirmation)
  expect(finish).toHaveProperty('disabled', false)
  expect(screen.queryByText(hint)).toBeNull()
  fireEvent.click(confirmation)
  expect(finish).toHaveProperty('disabled', true)
})

// Each note's message is made up, so only its code can keep the pending one out
it('leaves out the note that results are pending, by its code', () => {
  review({
    ...transcript,
    warnings: [
      { code: 'results_pending', message: 'Two made-up results are still to come.' },
      { code: 'recent_year_missing', message: 'This made-up record has no courses for last year.' },
    ],
  })
  expect(screen.getByText('No Courses Last Year')).toBeTruthy()
  expect(screen.queryByText("Some Results Aren't Out Yet")).toBeNull()
  expect(screen.queryByText('Two made-up results are still to come.')).toBeNull()
})
