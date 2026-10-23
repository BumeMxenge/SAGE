// The questionnaire's rules, worked out from the plans each answer keeps, which the API sends with
// every option, so no rule about timetables is copied here. The questions narrow in the order they
// come: an answer can't be chosen when it keeps none of the plans the answers before it keep, and
// changing an answer clears any later one that then keeps none, so the answers sent always keep a
// plan.
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

// The plans that every answer to the first `count` questions keeps, out of all her plans
export function keptBy(plans: string[], questions: Question[], answers: Answers, count = questions.length): string[] {
  return questions.slice(0, count).reduce((kept, question) => {
    const option = chosen(question, answers)
    return option ? kept.filter((plan) => option.keeps.includes(plan)) : kept
  }, plans)
}

// Why an option can't be chosen, or undefined when it can: it keeps none of the plans the answers
// before its question keep. SAGE asks two questions, so the clash is with the one answer before it.
export function clash(plans: string[], questions: Question[], answers: Answers, index: number, option: Option): string | undefined {
  const kept = keptBy(plans, questions, answers, index)
  if (option.keeps.some((plan) => kept.includes(plan))) return undefined
  const before = questions.slice(0, index).flatMap((question) => chosen(question, answers) ?? [])
  return `No plan has both ${before.map(({ label }) => `‘${label}’`).join(' and ')} and ‘${option.label}’.`
}

// Her answers once she chooses an option for the question at `index`, or clears it with null. Each
// later answer that then keeps none of the plans the answers before it keep is cleared.
export function choose(plans: string[], questions: Question[], answers: Answers, index: number, option: string | null): Answers {
  const next: Answers = { ...answers, [questions[index].id]: option ?? undefined }
  for (let later = index + 1; later < questions.length; later++) {
    const answer = chosen(questions[later], next)
    if (answer && clash(plans, questions, next, later, answer)) next[questions[later].id] = undefined
  }
  return next
}
