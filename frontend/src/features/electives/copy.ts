// Explore Electives' words: each tab's label and the line under its heading, as the planner prototype
// writes them, and the page's own. A Record over the API's tabs, so a tab the API adds fails the
// build until it has words here.
import type { components } from '@/lib/api-types.ts'

export type ElectiveTab = components['schemas']['Tab']['key']

export const tabWords: Record<ElectiveTab, { label: string; sub: string }> = {
  arts: { label: 'Art, Music & Aesthetics', sub: 'Visual art and music' },
  business: { label: 'Business & Management', sub: 'Marketing, people and how organisations run' },
  econ: { label: 'Economics & Finance', sub: 'Markets, money and managing your own finances' },
  ethics: { label: 'Ethics, Politics & Values', sub: 'Morality, justice and how we ought to live' },
  history: { label: 'The Past: History, Myth & the Ancient World', sub: 'Ancient civilisations, myth and world history' },
  languages: { label: 'Languages', sub: 'Learn to speak, read and write a new language' },
  literature: { label: 'Literature & Language', sub: 'Reading, writing and how language works' },
  logic: { label: 'Logic, Knowledge & Critical Thinking', sub: 'Reasoning and the foundations of knowledge' },
  media: { label: 'Film, Media & Communication', sub: 'Screen culture and how media shapes us' },
  religion: { label: 'Religion & Belief', sub: 'Traditions, texts and the study of faith' },
  science: { label: 'Science & the Living World', sub: 'Biology, the Earth, human origins and biomedical engineering' },
  society: { label: 'Society & Human Behaviour', sub: 'People, groups and how we think' },
}

export const searchPlaceholder = 'Search electives by code, topic or lecturer'

export const heartFailed = "Your favourite didn't save."

// The filtered page's line, over the cards that fit one of her plans
export const fitting = (count: number, plan: string) =>
  `Showing the ${count} ${count === 1 ? 'course' : 'courses'} that fit ${plan}.`

export const showEveryCourse = 'Show Every Course'

export const notCurrent = "This plan isn't one of your current plans, so every course is shown."

export const nothingFits = 'No Course Fits This Plan'

export const noMatch = 'No Courses Match'

export const noMatchMessage = (search: string) => `Nothing matches “${search}”. Try another word, or clear the search.`
