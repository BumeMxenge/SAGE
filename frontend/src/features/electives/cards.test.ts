// What a card says and which tab and cards Explore Electives shows, on made-up cards. The words and
// choices are written out by hand from the prototype and my card rules.
import { describe, expect, it } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { codesOf, convenersOf, keeping, matches, openingTab, putFirst, termsOf, withHeart } from './cards.ts'

type Elective = components['schemas']['Elective']
type Offering = components['schemas']['Offering']
type Tab = components['schemas']['Tab']

const offering = (code: string, fields: Partial<Offering> = {}): Offering => ({
  code,
  term: code.endsWith('S') ? 'sem2' : 'sem1',
  convener: null,
  hearted: false,
  can_heart: true,
  plans: [],
  ...fields,
})

const card = (offerings: Offering[], fields: Partial<Elective> = {}): Elective => ({
  codes: offerings.map((each) => each.code),
  name: 'Made-up Course',
  credits: 18,
  summary: null,
  hearted: offerings.some((each) => each.hearted),
  can_heart: offerings.some((each) => each.can_heart),
  note: null,
  offerings,
  ...fields,
})

describe("a card's words", () => {
  it('codes a course offered in both semesters BUS1036F/S, and says when it runs', () => {
    const both = card([offering('BUS1036F'), offering('BUS1036S')])
    expect(codesOf(both)).toBe('BUS1036F/S')
    expect(termsOf(both)).toBe('Semester 1 or 2')
    expect(codesOf(card([offering('SLL1002S')]))).toBe('SLL1002S')
    expect(termsOf(card([offering('SLL1002S')]))).toBe('Semester 2')
    expect(termsOf(card([offering('AGE1005L', { term: 'winter' })]))).toBe('Winter')
  })

  it('names one convener when the offerings share one, and each beside its term when they differ', () => {
    const shared = card([offering('BUS1036F', { convener: 'A Person' }), offering('BUS1036S', { convener: 'A Person' })])
    expect(convenersOf(shared)).toBe('Convener: A Person')
    const differ = card([offering('ECO1010F', { convener: 'R Chetty' }), offering('ECO1010S', { convener: 'N Narker' })])
    expect(convenersOf(differ)).toBe('Conveners: R Chetty (Sem 1), N Narker (Sem 2)')
    // An offering with no convener is left out, and none at all says nothing
    const one = card([offering('ECO1010F', { convener: 'R Chetty' }), offering('ECO1010S')])
    expect(convenersOf(one)).toBe('Convener: R Chetty (Sem 1)')
    expect(convenersOf(card([offering('ECO1010F'), offering('ECO1010S')]))).toBeNull()
  })
})

describe('what the page shows', () => {
  const french = card([offering('SLL1017F', { convener: 'Dr Made Up' }), offering('SLL1017S')], { name: 'French 1A' })
  const ethics = card([offering('PHI1010S')], { name: 'Ethics', summary: 'An introduction to moral philosophy.' })
  const tabs: Tab[] = [
    { key: 'languages', courses: [french] },
    { key: 'ethics', courses: [ethics] },
  ]

  it('matches a search in any case by code, name, summary or convener', () => {
    expect(matches(french, 'sll1017s')).toBe(true)
    expect(matches(french, 'SLL1017F/S')).toBe(true)
    expect(matches(ethics, 'MORAL')).toBe(true)
    expect(matches(french, 'made up')).toBe(true)
    expect(matches(french, 'moral')).toBe(false)
    expect(matches(french, '  ')).toBe(true)
  })

  it('hides a tab with nothing kept, and opens the address tab only if it is shown', () => {
    const kept = keeping(tabs, (each) => matches(each, 'moral'))
    expect(kept.map((tab) => tab.key)).toEqual(['ethics'])
    const none = () => false
    // The address names languages, which the search hides, so the first tab with a match opens
    expect(openingTab(kept, 'languages', none)).toBe('ethics')
    expect(openingTab(tabs, 'ethics', none)).toBe('ethics')
    expect(openingTab(tabs, null, none)).toBe('languages')
    expect(openingTab([], 'ethics', none)).toBeNull()
  })

  it('opens the first tab with a card that comes first, such as a favourite, when the address names none', () => {
    const first = (each: Elective) => each === ethics
    expect(openingTab(tabs, null, first)).toBe('ethics')
    expect(openingTab(tabs, 'languages', first)).toBe('languages')
    expect(putFirst([french, ethics], first)).toEqual([ethics, french])
  })
})

describe('a heart, before the API answers', () => {
  it('hearts each offering she can heart, and unhearting unhearts every one', () => {
    const pair = card([offering('BUS1036F'), offering('BUS1036S', { can_heart: false })])
    const other = card([offering('PHI1010S')])
    const electives = { tabs: [{ key: 'business' as const, courses: [pair, other] }] }
    const hearted = withHeart(electives, pair, true).tabs[0].courses
    expect(hearted[0].offerings.map((each) => each.hearted)).toEqual([true, false])
    expect(hearted[0].hearted).toBe(true)
    expect(hearted[1]).toBe(other)
    const both = card([offering('BUS1036F', { hearted: true }), offering('BUS1036S', { hearted: true, can_heart: false })])
    const unhearted = withHeart({ tabs: [{ key: 'business', courses: [both] }] }, both, false).tabs[0].courses[0]
    expect(unhearted.offerings.map((each) => each.hearted)).toEqual([false, false])
    expect(unhearted.hearted).toBe(false)
  })
})
