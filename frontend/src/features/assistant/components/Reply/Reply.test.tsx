// A reply as the assistant shows it, on made-up messages: its sources numbered in the order the API
// sends them, each over where its quote is, and none for a reply that quotes nothing; the line to her
// student advisor on a referral and not otherwise; and Open Plan, named from her set, linking to the
// plan alone at the term on screen, and left out when it names the plan already open alone. The
// texts and links are written out by hand.
import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import type { PlanAddress } from '@/lib/planAddress.ts'
import { Reply } from './Reply.tsx'

type Message = components['schemas']['Message']
type PlanSummary = components['schemas']['PlanSummary']

afterEach(cleanup)

// Made-up ids. The second plan is one her answers hid, which a reply may still offer.
const first = '00000000-0000-4000-8000-000000000001'
const second = '00000000-0000-4000-8000-000000000002'

const plans: PlanSummary[] = [
  { id: first, position: 1, name: 'Made-up Plan A', combination: null, hidden: false, credits: 138, to_choose: 0 },
  { id: second, position: 2, name: 'Made-up Plan B', combination: null, hidden: true, credits: 138, to_choose: 0 },
]

const alone: PlanAddress = { planId: first, compareWith: null, term: 'sem1', preview: null }

function replyOf(fields: Partial<Message>): Message {
  return {
    id: '00000000-0000-4000-8000-000000000011',
    role: 'assistant',
    content: 'A made-up reply.',
    term: 'sem1',
    created_at: '2026-10-23T10:00:00Z',
    referral: false,
    open_plan_id: null,
    citations: [],
    ...fields,
  }
}

it('numbers its sources in the order the API sends them, each over where its quote is', () => {
  const citations = [
    { position: 1, quote: 'A made-up first quote.', source: 'Made-up Handbook 2026', section: 'Made-up Rules', page: 58 },
    { position: 2, quote: 'A made-up second quote.', source: 'Made-up Handbook 2026', section: 'Made-up Curriculum', page: 61 },
  ]
  render(<Reply reply={replyOf({ citations })} plans={plans} address={alone} />)
  const sources = screen.getByRole('list', { name: 'Sources' })
  expect(sources.tagName).toBe('OL')
  expect(within(sources).getAllByRole('listitem').map((item) => item.textContent)).toEqual([
    'A made-up first quote.Made-up Handbook 2026, Made-up Rules, page 58',
    'A made-up second quote.Made-up Handbook 2026, Made-up Curriculum, page 61',
  ])
})

it('shows no sources for a reply that quotes nothing', () => {
  render(<Reply reply={replyOf({ citations: [] })} plans={plans} address={alone} />)
  expect(screen.queryByText('Sources')).toBeNull()
})

it('adds the line to her student advisor on a referral, and not otherwise', () => {
  const { rerender } = render(<Reply reply={replyOf({ referral: true })} plans={plans} address={alone} />)
  expect(screen.getByText('Your student advisor can help with this.')).toBeTruthy()
  rerender(<Reply reply={replyOf({ referral: false })} plans={plans} address={alone} />)
  expect(screen.queryByText('Your student advisor can help with this.')).toBeNull()
})

it('opens the plan it offers alone, named from her set, at the term on screen, from compare too', () => {
  const comparing: PlanAddress = { planId: first, compareWith: second, term: 'sem2', preview: null }
  render(<Reply reply={replyOf({ open_plan_id: second })} plans={plans} address={comparing} />)
  const link = screen.getByRole('link', { name: 'Open Made-up Plan B' })
  expect(link.getAttribute('href')).toBe('/plan/00000000-0000-4000-8000-000000000002?term=sem2')
})

it('leaves Open Plan out when it names the plan already open alone, and links any other', () => {
  const { rerender } = render(<Reply reply={replyOf({ open_plan_id: first })} plans={plans} address={alone} />)
  expect(screen.queryByRole('link')).toBeNull()
  rerender(<Reply reply={replyOf({ open_plan_id: second })} plans={plans} address={alone} />)
  const link = screen.getByRole('link', { name: 'Open Made-up Plan B' })
  expect(link.getAttribute('href')).toBe('/plan/00000000-0000-4000-8000-000000000002')
})
