// The questionnaire's rules, worked out from the plans each answer keeps, which the API sends with
// every option, so no rule about timetables is copied here. An answer can't be chosen when it keeps
// none of the plans her answers to the other questions keep, whichever she chose first, as in the
// prototype. So every answer she can choose leaves a plan, and choosing one never clears another.
import type { components } from '@/lib/api-types.ts'

type Question = components['schemas']['Question']
type Option = components['schemas']['Option']

// The option chosen for each question, by its id. A question left unanswered narrows nothing.
export type Answers = Partial<Record<Question['id'], string>>

// The questions worth asking: those with an answer that keeps fewer than all her plans. The API also
// sends a question whose only answer is no preference, which would narrow nothing (docs/shortfalls.md).
export function askable(questions: Question[], planCount: number): Question[] {
  return questions.filter((question) => question.options.some((option) => option.keeps.length < planCount))
}

function chosen(question: Question, answers: Answers): Option | undefined {
  return question.options.find((option) => option.id === answers[question.id])
}

// The plans that every answer keeps, out of all her plans
export function keptBy(plans: string[], questions: Question[], answers: Answers): string[] {
  return questions.reduce((kept, question) => {
    const option = chosen(question, answers)
    return option ? kept.filter((plan) => option.keeps.includes(plan)) : kept
  }, plans)
}

// Why an option can't be chosen, or undefined when it can: it keeps none of the plans her answers to
// the other questions keep. Its own question's answer is left out, as choosing the option replaces it.
// SAGE asks two questions, so the clash is with the one other answer.
export function clash(plans: string[], questions: Question[], answers: Answers, question: Question, option: Option): string | undefined {
  const others: Answers = { ...answers, [question.id]: undefined }
  const kept = keptBy(plans, questions, others)
  if (option.keeps.some((plan) => kept.includes(plan))) return undefined
  const blocking = questions.flatMap((each) => chosen(each, others) ?? [])
  return `No plan has both ${blocking.map(({ label }) => `‘${label}’`).join(' and ')} and ‘${option.label}’.`
}
