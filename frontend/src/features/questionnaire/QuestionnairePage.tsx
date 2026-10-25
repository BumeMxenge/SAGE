// The questionnaire, which /plan shows while her plan set is too long to compare and isn't answered.
// It asks its questions on one page, as the prototype does, each with its answers in the API's order,
// so she sees the other question's answers grey out as she chooses one. Show My Plans saves the
// answers, which hide every plan they don't keep, and refreshes her set, so the plan workspace then
// opens the first plan they kept. Her set has arrived by the time the page shows, so its title and
// subtitle render straight away, over the questions' skeletons until the questions arrive. While her
// answers save and her set is read again, the page gives way to the plan's skeleton, which the plan
// workspace passes in, as features don't import each other. A save that fails brings her back to her
// answers as she left them.
import { useMutation, useQuery } from '@tanstack/react-query'
import { type ReactNode, useState } from 'react'
import { Button } from '@/components/actions/Button/Button.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { Arrival } from '@/components/feedback/Arrival/Arrival.tsx'
import { ChoiceChips } from '@/features/questionnaire/components/ChoiceChips/ChoiceChips.tsx'
import { ChoiceChipsSkeleton } from '@/features/questionnaire/components/ChoiceChips/ChoiceChipsSkeleton.tsx'
import { client, dataOf } from '@/lib/api.ts'
import type { components } from '@/lib/api-types.ts'
import { queries, refresh } from '@/lib/queryKeys.ts'
import { type Answers, askable, clash, keptBy } from './answers.ts'
import styles from './QuestionnairePage.module.css'

type PlanSet = components['schemas']['PlanSet']

// The line beside Show My Plans: how far her answers narrow her plans
function narrowing(kept: number, total: number, answered: boolean): string {
  if (!answered) return `Answer to narrow your ${total} plans, or carry on to keep them all.`
  if (kept === total) return `This keeps all ${total} of your plans.`
  return `This keeps ${kept} of your ${total} plans.`
}

type QuestionnairePageProps = { set: PlanSet; saving: ReactNode }

export function QuestionnairePage({ set, saving }: QuestionnairePageProps) {
  const read = useQuery(queries.questionnaire())
  const [answers, setAnswers] = useState<Answers>({})
  const save = useMutation({
    // Each answer is the id of one of the options the API sent for its question
    mutationFn: (body: Answers) =>
      dataOf(client.POST('/v1/questionnaire', { body: body as components['schemas']['Answers'] })),
    // Her set comes back answered, so the plan workspace opens the first plan the answers kept
    onSuccess: () => refresh.questionnaireAnswered(),
    // Answered already, as in another tab, or no longer needed: her set moves on the same way. The
    // other refusals wait for the app's in-page error states (docs/shortfalls.md).
    onError: async (error) => {
      if (error.code === 'questionnaire_answered' || error.code === 'questionnaire_not_needed') {
        await refresh.questionnaireAnswered()
      }
    },
  })
  if (save.isPending) return saving

  const plans = set.plans.map((plan) => plan.id)
  return (
    <div className={styles.page}>
      <PageHeader
        title="A Few Questions First"
        subtitle={`SAGE found ${plans.length} plans for ${set.period}. Your answers narrow them to a short list.`}
      />
      <Arrival
        data={read.data}
        waiting={read.isPending}
        // The course question, with its hint, then the week's, in their shape
        skeleton={
          <div className={styles.questions}>
            <ChoiceChipsSkeleton label={36} description={28} chips={[24, 30, 20, 18]} />
            <ChoiceChipsSkeleton label={20} chips={[17, 26, 13]} />
          </div>
        }
        status="Loading your questions…"
      >
        {(questionnaire) => {
          const questions = askable(questionnaire.questions, plans.length)
          const answered = questions.some((each) => answers[each.id] !== undefined)
          return (
            <>
              <div className={styles.questions}>
                {questions.map((question) => (
                  <ChoiceChips
                    key={question.id}
                    label={question.prompt}
                    description={question.hint ?? undefined}
                    choices={question.options.map((option) => ({
                      value: option.id,
                      label: option.label,
                      unavailable: clash(plans, questions, answers, question, option),
                    }))}
                    value={answers[question.id] ?? null}
                    onChange={(option) => setAnswers({ ...answers, [question.id]: option ?? undefined })}
                  />
                ))}
              </div>
              <div className={styles.actions}>
                <Button onPress={() => save.mutate(answers)}>Show My Plans</Button>
                {/* An output is a polite status, so a screen reader hears the new count as she answers */}
                <output className={styles.narrowing}>
                  {narrowing(keptBy(plans, questions, answers).length, plans.length, answered)}
                </output>
              </div>
            </>
          )
        }}
      </Arrival>
    </div>
  )
}
