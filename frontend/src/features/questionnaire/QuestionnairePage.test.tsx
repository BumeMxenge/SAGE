// The questionnaire reads its questions from the shared cache, so a heart changed elsewhere, whose
// refresh fetches them again (queryKeys.ts), reaches it: the hearted course moves first, as the API
// lists it, and shows its heart. The set and the questions are made up.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { queries } from '@/lib/queryKeys.ts'
import { QuestionnairePage } from './QuestionnairePage.tsx'

type PlanSet = components['schemas']['PlanSet']
type Questionnaire = components['schemas']['Questionnaire']
type Option = components['schemas']['Option']

afterEach(cleanup)

const plans = Array.from({ length: 6 }, (_, index) => ({
  id: `00000000-0000-4000-8000-00000000000${index + 1}`,
  position: index + 1,
  name: `Made-up Plan ${index + 1}`,
  combination: null,
  hidden: false,
  credits: 144,
}))
const set: PlanSet = { period: 2026, version: 1, questionnaire_needed: true, reasons: [], plans }
const ids = plans.map((plan) => plan.id)

const courseA: Option = { id: 'TST4001F', label: 'Made-up Course A', hearted: false, keeps: ids.slice(0, 3) }
const courseB: Option = { id: 'TST4002S', label: 'Made-up Course B', hearted: false, keeps: ids.slice(3) }
const noPreference: Option = { id: 'no_preference', label: 'No strong preference', hearted: false, keeps: ids }

// As the API answers: hearted courses first, then the rest by code
function questionnaire(options: Option[]): Questionnaire {
  return {
    needed: true,
    questions: [{ id: 'course', prompt: 'Is there a course you already know you want?', hint: null, options }],
  }
}

it('shows a heart changed elsewhere, with the hearted course first, as the API lists it', async () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } })
  queryClient.setQueryData(queries.questionnaire().queryKey, questionnaire([courseA, courseB, noPreference]))
  render(
    <QueryClientProvider client={queryClient}>
      <QuestionnairePage set={set} />
    </QueryClientProvider>,
  )
  const answers = () => screen.getAllByRole('radio').map((answer) => answer.textContent)
  expect(answers()).toEqual(['Made-up Course A', 'Made-up Course B', 'No strong preference'])

  // Course B hearted in Explore Electives, and the questions fetched again. The cache tells the page
  // on its next tick.
  queryClient.setQueryData(queries.questionnaire().queryKey, questionnaire([{ ...courseB, hearted: true }, courseA, noPreference]))
  await screen.findByRole('radio', { name: 'Made-up Course B, favourite' })
  expect(answers()).toEqual(['Made-up Course B, favourite', 'Made-up Course A', 'No strong preference'])
})
