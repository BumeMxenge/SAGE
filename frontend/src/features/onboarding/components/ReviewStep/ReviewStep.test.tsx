// Finish Setup waits for the student to confirm their last year: disabled before the box is ticked,
// enabled once it is, and disabled again when it is unticked
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
  // Each year opens at the top of the page, which jsdom can't scroll
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

it('keeps Finish Setup disabled until the last year is confirmed', () => {
  // The catalogue is already read, so nothing goes to the network
  const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
  queryClient.setQueryData(queries.catalogue().queryKey, catalogue)
  render(
    <QueryClientProvider client={queryClient}>
      <ReviewStep transcript={transcript} onSaved={async () => {}} />
    </QueryClientProvider>,
  )
  const finish = screen.getByRole('button', { name: 'Finish Setup' })
  const confirmation = screen.getByRole('checkbox', { name: 'This reflects my current academic record' })

  expect(finish).toHaveProperty('disabled', true)
  fireEvent.click(confirmation)
  expect(finish).toHaveProperty('disabled', false)
  fireEvent.click(confirmation)
  expect(finish).toHaveProperty('disabled', true)
})
