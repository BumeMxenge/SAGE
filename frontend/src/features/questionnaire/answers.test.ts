// The questionnaire's rules, on made-up questions about six made-up plans. Each expected value is
// worked out by hand from the plans each answer keeps, in the comment beside it.
import { expect, it } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { type Answers, askable, clash, keptBy } from './answers.ts'

type Question = components['schemas']['Question']
type Option = components['schemas']['Option']

const plans = ['plan-1', 'plan-2', 'plan-3', 'plan-4', 'plan-5', 'plan-6']
const keeping = (...numbers: number[]) => numbers.map((number) => `plan-${number}`)
const option = (id: string, label: string, keeps: string[]): Option => ({ id, label, keeps })

const noPreference = option('no_preference', 'No preference', plans)
const courseA = option('TST4001F', 'Made-up Course A', keeping(1, 2, 3))
const courseB = option('TST4002S', 'Made-up Course B', keeping(3, 4))
const courseC = option('TST4003F', 'Made-up Course C', keeping(5, 6))
const fewest = option('fewest_8am', 'Fewest 8am starts', keeping(1, 4))
const lunch = option('lunch_free', 'Keep the 13:00 lunch hour free', keeping(5))

const course: Question = {
  id: 'course',
  prompt: 'Is there a course you already know you want?',
  hint: null,
  options: [courseA, courseB, courseC, noPreference],
}
const week: Question = { id: 'week', prompt: 'How should the week feel?', hint: null, options: [fewest, lunch, noPreference] }
const questions = [course, week]

it('greys out an answer that keeps none of the plans the other answer keeps, and only that', () => {
  const answers: Answers = { course: courseA.id }
  // Course A keeps plans 1 to 3, and Fewest 8am starts keeps 1 and 4: they share plan 1
  expect(clash(plans, questions, answers, week, fewest)).toBeUndefined()
  // The free lunch hour keeps plan 5 alone, which course A doesn't keep
  expect(clash(plans, questions, answers, week, lunch)).toBe(
    'No plan has both ‘Made-up Course A’ and ‘Keep the 13:00 lunch hour free’.',
  )
  expect(clash(plans, questions, answers, week, noPreference)).toBeUndefined()
})

it('greys out an answer to the first question when the second was chosen first', () => {
  const answers: Answers = { week: lunch.id }
  // The free lunch hour keeps plan 5 alone: course A keeps 1 to 3, and course C keeps 5 and 6
  expect(clash(plans, questions, answers, course, courseA)).toBe(
    'No plan has both ‘Keep the 13:00 lunch hour free’ and ‘Made-up Course A’.',
  )
  expect(clash(plans, questions, answers, course, courseC)).toBeUndefined()
})

it("never greys out an answer against its own question's answer", () => {
  // Course C keeps plans 5 and 6, none of which course A keeps, but choosing C replaces A
  expect(clash(plans, questions, { course: courseA.id }, course, courseC)).toBeUndefined()
})

it('keeps the plans that every answer keeps', () => {
  expect(keptBy(plans, questions, {})).toEqual(plans)
  // Course A keeps 1 to 3, and Fewest 8am starts 1 and 4: plan 1 is in both
  expect(keptBy(plans, questions, { course: courseA.id, week: fewest.id })).toEqual(keeping(1))
  expect(keptBy(plans, questions, { week: lunch.id })).toEqual(keeping(5))
})

it('asks only a question with an answer that would narrow her plans', () => {
  const nothingToChoose: Question = { ...week, options: [noPreference] }
  // Keeping five of the six plans narrows them by one
  const narrowsByOne: Question = { ...week, options: [option('lunch_free', 'Keep the 13:00 lunch hour free', keeping(1, 2, 3, 4, 5)), noPreference] }
  expect(askable([course, nothingToChoose], plans.length)).toEqual([course])
  expect(askable([course, narrowsByOne], plans.length)).toEqual([course, narrowsByOne])
})
