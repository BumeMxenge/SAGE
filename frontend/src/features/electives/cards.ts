// What a card says and which cards and tab the page shows, worked out from the API's cards with no
// markup. Which offerings fit, which she can heart and what a note says are the API's: these only
// word them, filter by them and order them.
import type { components } from '@/lib/api-types.ts'
import { termLabels } from '@/lib/copy.ts'

type Electives = components['schemas']['Electives']
type Elective = components['schemas']['Elective']
type Tab = components['schemas']['Tab']
type TermCode = components['schemas']['Offering']['term']

// A course's codes as the prototype writes a course offered more than once: ECO1010F/S
export function codesOf({ codes }: Elective): string {
  return `${codes[0]}${codes
    .slice(1)
    .map((code) => `/${code.slice(7)}`)
    .join('')}`
}

const termWords: Record<TermCode, string> = {
  q1: 'Quarter 1',
  q2: 'Quarter 2',
  q3: 'Quarter 3',
  q4: 'Quarter 4',
  sem1: 'Semester 1',
  sem2: 'Semester 2',
  full_year: 'Full year',
  winter: 'Winter',
  summer: 'Summer',
  other: 'Other',
}

// When the course runs: "Semester 2", or for one offered in both semesters "Semester 1 or 2"
export function termsOf({ offerings }: Elective): string {
  const terms = offerings.map((offering) => offering.term)
  if (terms.length > 1 && terms.every((term) => term === 'sem1' || term === 'sem2')) {
    return `Semester ${terms.map((term) => term.slice(3)).join(' or ')}`
  }
  return terms.map((term) => termWords[term]).join(' or ')
}

// "Convener: A" when the offerings share one, otherwise "Conveners: A (Sem 1), B (Sem 2)", leaving
// out an offering with none. Nothing when none names one.
export function convenersOf({ offerings }: Elective): string | null {
  const named = offerings.flatMap((offering) => (offering.convener ? [offering] : []))
  if (named.length === 0) return null
  if (named.length === offerings.length && named.every((offering) => offering.convener === named[0].convener)) {
    return `Convener: ${named[0].convener}`
  }
  const each = named.map((offering) => `${offering.convener} (${termLabels[offering.term]})`).join(', ')
  return `${named.length === 1 ? 'Convener' : 'Conveners'}: ${each}`
}

// Whether a card matches the search, by its codes, name, summary or conveners, in any case
export function matches(card: Elective, search: string): boolean {
  const wanted = search.trim().toLowerCase()
  const words = [...card.codes, codesOf(card), card.name, card.summary ?? '', ...card.offerings.map((offering) => offering.convener ?? '')]
  return words.join(' ').toLowerCase().includes(wanted)
}

// Whether one of the card's offerings fits the plan, as the API lists the plans each fits
export const fits = (card: Elective, planId: string) => card.offerings.some((offering) => offering.plans.includes(planId))

// Each tab with only the cards kept, leaving out a tab with none
export function keeping(tabs: Tab[], kept: (card: Elective) => boolean): Tab[] {
  return tabs.flatMap((tab) => {
    const courses = tab.courses.filter(kept)
    return courses.length > 0 ? [{ ...tab, courses }] : []
  })
}

// The cards that come first, such as the favourites she had as the page opened, ahead of the rest,
// each group in the API's order
export const putFirst = (courses: Elective[], first: (card: Elective) => boolean) => [
  ...courses.filter(first),
  ...courses.filter((card) => !first(card)),
]

// The tab on screen: the address's, if it's shown, else the first tab with a card that comes first,
// such as a favourite on the filtered page, else the first tab
export function openingTab(tabs: Tab[], asked: string | null, first: (card: Elective) => boolean): string | null {
  const named = tabs.find((tab) => tab.key === asked) ?? tabs.find((tab) => tab.courses.some(first)) ?? tabs.at(0)
  return named?.key ?? null
}

// The electives as the heart routes will leave them once one card is hearted or unhearted: hearting
// hearts each offering she can heart, and unhearting unhearts every one
export function withHeart(electives: Electives, card: Elective, heart: boolean): Electives {
  const changed = (course: Elective): Elective => {
    const offerings = course.offerings.map((offering) => ({ ...offering, hearted: heart && (offering.hearted || offering.can_heart) }))
    return { ...course, offerings, hearted: offerings.some((offering) => offering.hearted) }
  }
  return {
    tabs: electives.tabs.map((tab) => ({
      ...tab,
      courses: tab.courses.map((course) => (course.codes[0] === card.codes[0] ? changed(course) : course)),
    })),
  }
}
