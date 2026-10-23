// The questionnaire, which /plan shows while her plan set is too long to compare and isn't answered.
// It asks one question at a time, each with its answers in the API's order, which lists hearted
// courses first. Show My Plans saves the answers, which hide every plan they don't keep, and
// refreshes her set, so the plan workspace then opens the first plan they kept.
import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Button } from '@/components/actions/Button/Button.tsx'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { ChoiceChips } from '@/components/inputs/ChoiceChips/ChoiceChips.tsx'
import { client, dataOf } from '@/lib/api.ts'
import type { components } from '@/lib/api-types.ts'
import { queries, refresh } from '@/lib/queryKeys.ts'
import { type Answers, askable, choose, clash, keptBy } from './answers.ts'
import styles from './QuestionnairePage.module.css'

type PlanSet = components['schemas']['PlanSet']

// The line beside the step's button: how far her answers narrow her plans
function narrowing(kept: number, total: number, answered: boolean): string {
  if (!answered) return `Answer to narrow your ${total} plans, or carry on to keep them all.`
  if (kept === total) return `This keeps all ${total} of your plans.`
  return `This keeps ${kept} of your ${total} plans.`
}

export function QuestionnairePage({ set }: { set: PlanSet }) {
  const { data: questionnaire } = useQuery(queries.questionnaire())
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Answers>({})
  // Focus follows Next and Back to the new question, never the page opening
  const [moved, setMoved] = useState(false)
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
  // Nothing shows until the questions arrive. Its loading state comes with the app's others.
  if (!questionnaire) return null

  const plans = set.plans.map((plan) => plan.id)
  const questions = askable(questionnaire.questions, plans.length)
  const question = questions.at(step)
  const answered = questions.some((each) => answers[each.id] !== undefined)

  function move(to: number) {
    setStep(to)
    setMoved(true)
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="A Few Questions First"
        subtitle={`SAGE found ${plans.length} plans for ${set.period}. Your answers narrow them to a short list, and the rest stay at the foot of your plan list.`}
      />
      {question && (
        // A new question's chips are new chips, so the one that takes focus takes it as they appear
        <ChoiceChips
          key={question.id}
          label={question.prompt}
          description={question.hint ?? undefined}
          choices={question.options.map((option) => ({
            value: option.id,
            label: option.hearted ? (
              <>
                {option.label}
                <Icon name="favorite" filled />
                <span className="visually-hidden">, favourite</span>
              </>
            ) : (
              option.label
            ),
            unavailable: clash(plans, questions, answers, step, option),
          }))}
          value={answers[question.id] ?? null}
          onChange={(option) => setAnswers(choose(plans, questions, answers, step, option))}
          takeFocus={moved}
        />
      )}
      <div className={styles.actions}>
        {step > 0 && (
          <Button variant="quiet" icon="chevron_left" onPress={() => move(step - 1)}>
            Back
          </Button>
        )}
        {step < questions.length - 1 ? (
          <Button onPress={() => move(step + 1)}>Next</Button>
        ) : (
          // Disabled while the answers are saving, so a second press can't send them again
          <Button isDisabled={save.isPending} onPress={() => save.mutate(answers)}>
            Show My Plans
          </Button>
        )}
        {/* An output is a polite status, so a screen reader hears the new count as she answers */}
        <output className={styles.narrowing}>
          {narrowing(keptBy(plans, questions, answers).length, plans.length, answered)}
        </output>
      </div>
    </div>
  )
}
