// The questionnaire's rules, on made-up questions about six made-up plans. Each expected value is
// worked out by hand from the plans each answer keeps, in the comment beside it.
import { expect, it } from 'vitest'
import type { components } from '@/lib/api-types.ts'
import { type Answers, askable, choose, clash, keptBy } from './answers.ts'

type Question = components['schemas']['Question']
type Option = components['schemas']['Option']

const plans = ['plan-1', 'plan-2', 'plan-3', 'plan-4', 'plan-5', 'plan-6']
const keeping = (...numbers: number[]) => numbers.map((number) => `plan-${number}`)
const option = (id: string, label: string, keeps: string[]): Option => ({ id, label, hearted: false, keeps })

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

it('greys out a later answer that keeps none of the plans the earlier one keeps, and only that', () => {
  const answers: Answers = { course: courseA.id }
  // Course A keeps plans 1 to 3, and Fewest 8am starts keeps 1 and 4: they share plan 1
  expect(clash(plans, questions, answers, 1, fewest)).toBeUndefined()
  // The free lunch hour keeps plan 5 alone, which course A doesn't keep
  expect(clash(plans, questions, answers, 1, lunch)).toBe(
    'No plan has both ‘Made-up Course A’ and ‘Keep the 13:00 lunch hour free’.',
  )
  expect(clash(plans, questions, answers, 1, noPreference)).toBeUndefined()
})

it('never greys out an answer to the first question, whatever is answered', () => {
  // Course C keeps plans 5 and 6, which neither course A, chosen for this question, nor Fewest 8am
  // starts, chosen for the next, keeps
  const answers: Answers = { course: courseA.id, week: fewest.id }
  for (const each of course.options) expect(clash(plans, questions, answers, 0, each)).toBeUndefined()
})

it('keeps the plans that every answer keeps', () => {
  expect(keptBy(plans, questions, {})).toEqual(plans)
  // Course A keeps 1 to 3, and Fewest 8am starts 1 and 4: plan 1 is in both
  expect(keptBy(plans, questions, { course: courseA.id, week: fewest.id })).toEqual(keeping(1))
  // The answers before the week question alone: course B's plans 3 and 4
  expect(keptBy(plans, questions, { course: courseB.id, week: fewest.id }, 1)).toEqual(keeping(3, 4))
  expect(keptBy(plans, questions, { week: lunch.id })).toEqual(keeping(5))
})

it('clears a later answer that keeps no plan with a changed earlier one, and only that', () => {
  const answers: Answers = { course: courseA.id, week: fewest.id }
  // Course B keeps plans 3 and 4, and Fewest 8am starts still shares plan 4
  expect(choose(plans, questions, answers, 0, courseB.id)).toEqual({ course: courseB.id, week: fewest.id })
  // Course C keeps plans 5 and 6, and Fewest 8am starts keeps neither
  expect(choose(plans, questions, answers, 0, courseC.id)).toEqual({ course: courseC.id, week: undefined })
  // With no course chosen every plan is kept, so the week's answer stays
  expect(choose(plans, questions, answers, 0, null)).toEqual({ course: undefined, week: fewest.id })
})

it('asks only a question with an answer that would narrow her plans', () => {
  const nothingToChoose: Question = { ...week, options: [noPreference] }
  // Keeping five of the six plans narrows them by one
  const narrowsByOne: Question = { ...week, options: [option('lunch_free', 'Keep the 13:00 lunch hour free', keeping(1, 2, 3, 4, 5)), noPreference] }
  expect(askable([course, nothingToChoose], plans.length)).toEqual([course])
  expect(askable([course, narrowsByOne], plans.length)).toEqual([course, narrowsByOne])
})
