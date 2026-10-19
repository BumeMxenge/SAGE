// The review: the course history read from the transcript, one year at a time, for the student to
// check, correct and confirm. Their programme comes from the transcript, or they choose it, and notes
// that came with the reading show above. In edit mode they can change an outcome, remove a course or
// add one from the catalogue, each after a question that says what will change. On the last year, once
// they tick that it reflects their record, Finish Setup sends the whole history in one request.
import { useMutation, useQuery } from '@tanstack/react-query'
import { useReducer, useState } from 'react'
import { Button } from '@/components/actions/Button/Button.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { Checkbox } from '@/components/inputs/Checkbox/Checkbox.tsx'
import { Select } from '@/components/inputs/Select/Select.tsx'
import { SelectItem } from '@/components/inputs/Select/SelectItem.tsx'
import { ConfirmChange } from '@/features/onboarding/components/ConfirmChange/ConfirmChange.tsx'
import { CoursePicker } from '@/features/onboarding/components/CoursePicker/CoursePicker.tsx'
import { YearTable } from '@/features/onboarding/components/YearTable/YearTable.tsx'
import { focusOnOpen } from '@/features/onboarding/focusOnOpen.ts'
import { type ReviewAction, type ReviewLine, reviewReducer, setupOf, startReview } from '@/features/onboarding/review.ts'
import { client, dataOf } from '@/lib/api.ts'
import type { components } from '@/lib/api-types.ts'
import { termLabels } from '@/lib/copy.ts'
import { queries } from '@/lib/queryKeys.ts'
import styles from './ReviewStep.module.css'

type Transcript = components['schemas']['Transcript']
type Course = components['schemas']['Course']

// A title for each note the reading can send, so a new kind of note fails the build until it has one
const warningTitles: Record<components['schemas']['TranscriptWarning']['code'], string> = {
  term_gpa_mismatch: "A Term Average Doesn't Match",
  recent_year_missing: 'No Courses Last Year',
  results_pending: "Some Results Aren't Out Yet",
}

// The question open over the review, if any: picking a course, or confirming one change
type Question =
  | { kind: 'pick' }
  | { kind: 'add'; course: Course; result: string | null }
  | { kind: 'change'; line: ReviewLine; result: string }
  | { kind: 'remove'; line: ReviewLine }

const courses = (count: number) => `${count} ${count === 1 ? 'course' : 'courses'}`

type ReviewStepProps = { transcript: Transcript; onSaved: () => Promise<void> }

export function ReviewStep({ transcript, onSaved }: ReviewStepProps) {
  const [review, dispatch] = useReducer(reviewReducer, transcript, startReview)
  const [yearIndex, setYearIndex] = useState(0)
  const [editing, setEditing] = useState(false)
  const [question, setQuestion] = useState<Question | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const catalogue = useQuery(queries.catalogue())
  const saving = useMutation({
    mutationFn: (setup: components['schemas']['Setup']) => dataOf(client.POST('/v1/onboarding/complete', { body: setup })),
    onSuccess: onSaved,
  })

  // The years come from the transcript, so a year stays even if its courses are all removed
  const years = [...new Set(transcript.lines.map((line) => line.academic_year))].toSorted((first, second) => first - second)
  const year = years[yearIndex]
  const isLast = yearIndex === years.length - 1
  const lines = review.lines.filter((line) => line.academic_year === year)
  const credits = lines.reduce((total, line) => total + line.credits, 0)
  const caption = `${year} · Year ${yearIndex + 1} of ${years.length}`
  const programme = transcript.curriculum_options.length === 1 ? transcript.curriculum_options[0] : null
  const symbols = catalogue.data?.symbols ?? []
  const words = new Map(symbols.map((symbol) => [symbol.symbol, symbol.label]))
  const wordsFor = (result: string) => words.get(result) ?? result

  function apply(action: ReviewAction) {
    dispatch(action)
    setQuestion(null)
  }

  // Moving on waits for the student to finish editing. Finish Setup also needs the box ticked, a
  // programme, and at least one course, as the API can't save an empty history. The box sits just
  // above it; the rest say why it waits.
  const canFinish = confirmed && !editing && review.curriculum !== null && review.lines.length > 0 && !saving.isPending
  function nextHint(): string | null {
    if (editing) return 'Finish editing to continue.'
    if (!isLast) return null
    if (review.lines.length === 0) return 'Add at least one course to finish.'
    if (!review.curriculum) return 'Choose your programme to finish.'
    return null
  }
  const hint = nextHint()

  function finish() {
    if (review.curriculum) saving.mutate(setupOf(review.curriculum, review.lines))
  }

  return (
    <div className={styles.review}>
      <PageHeader
        title="Review Your Course History"
        subtitle={`We pulled ${courses(transcript.lines.length)} out of your transcript. Confirm one year at a time. SAGE checks every prerequisite against this history, so anything wrong here follows you through registration.`}
      />
      <dl className={styles.programme}>
        <dt>Programme</dt>
        <dd>
          {programme ? (
            programme.name
          ) : (
            <Select
              label="Programme"
              placeholder="Choose your programme"
              selectedKey={review.curriculum}
              onSelectionChange={(code) => {
                if (code !== null) dispatch({ type: 'chooseCurriculum', code: String(code) })
              }}
            >
              {catalogue.data?.curricula.map((curriculum) => (
                <SelectItem key={curriculum.code} id={curriculum.code}>
                  {curriculum.name}
                </SelectItem>
              ))}
            </Select>
          )}
        </dd>
      </dl>
      {transcript.warnings.map((warning) => (
        <ErrorState
          key={warning.code}
          variant="inline"
          tone="warning"
          icon="info"
          title={warningTitles[warning.code]}
          message={warning.message}
        />
      ))}
      {/* Each year takes focus as it opens, so a screen reader hears which year it is */}
      <section key={year} ref={focusOnOpen} tabIndex={-1} aria-label={caption} className={styles.year}>
        <div className={styles.tools}>
          <p className={styles.summary}>
            {courses(lines.length)} · {credits} credits
          </p>
          {editing ? (
            <>
              <Button variant="quiet" icon="add" onPress={() => setQuestion({ kind: 'pick' })}>
                Add a Course
              </Button>
              <Button variant="secondary" onPress={() => setEditing(false)}>
                Done Editing
              </Button>
            </>
          ) : (
            <Button variant="secondary" onPress={() => setEditing(true)}>
              Edit Courses
            </Button>
          )}
        </div>
        <YearTable
          caption={caption}
          lines={lines}
          symbols={symbols}
          editing={editing}
          onChangeOutcome={(line, result) => setQuestion({ kind: 'change', line, result })}
          onRemove={(line) => setQuestion({ kind: 'remove', line })}
        />
      </section>
      {isLast && (
        <Checkbox isSelected={confirmed} onChange={setConfirmed}>
          This reflects my current academic record
        </Checkbox>
      )}
      <div className={styles.footer}>
        {yearIndex > 0 && (
          <Button variant="quiet" onPress={() => setYearIndex(yearIndex - 1)}>
            Back
          </Button>
        )}
        <div className={styles.next}>
          {hint && <p className={styles.hint}>{hint}</p>}
          {isLast ? (
            <Button isDisabled={!canFinish} onPress={finish}>
              Finish Setup
            </Button>
          ) : (
            <Button isDisabled={editing} onPress={() => setYearIndex(yearIndex + 1)}>
              Confirm {year}
            </Button>
          )}
        </div>
      </div>
      {question?.kind === 'pick' && (
        <CoursePicker
          year={year}
          courses={(catalogue.data?.courses ?? []).filter((course) => !lines.some((line) => line.course_code === course.code))}
          onClose={() => setQuestion(null)}
          onPick={(course) => setQuestion({ kind: 'add', course, result: null })}
        />
      )}
      {question?.kind === 'add' && (
        <ConfirmChange
          title="Add This Course?"
          lead="The term comes from the handbook."
          facts={[
            { term: 'Adding', value: `${question.course.code}: ${question.course.name}` },
            { term: 'Year', value: `${year}, ${termLabels[question.course.term]}` },
            {
              term: 'Outcome',
              value: (
                <Select
                  label={`Outcome for ${question.course.code}`}
                  placeholder="Set the outcome for this course"
                  selectedKey={question.result}
                  onSelectionChange={(result) => {
                    if (result !== null) setQuestion({ ...question, result: String(result) })
                  }}
                >
                  {symbols.map((symbol) => (
                    <SelectItem key={symbol.symbol} id={symbol.symbol} description={symbol.symbol}>
                      {symbol.label}
                    </SelectItem>
                  ))}
                </Select>
              ),
            },
          ]}
          cancelLabel="Back to List"
          confirmLabel="Add Course"
          isConfirmDisabled={question.result === null}
          onCancel={() => setQuestion({ kind: 'pick' })}
          onConfirm={() => {
            if (question.result !== null) apply({ type: 'add', year, course: question.course, result: question.result })
          }}
        />
      )}
      {question?.kind === 'change' && (
        <ConfirmChange
          title="Change This Outcome?"
          lead="Outcomes drive prerequisite checks."
          facts={[
            { term: 'Course', value: `${question.line.course_code}: ${question.line.course_name}` },
            { term: 'From', value: wordsFor(question.line.result) },
            { term: 'To', value: wordsFor(question.result) },
          ]}
          cancelLabel="Keep Outcome"
          confirmLabel="Change Outcome"
          onCancel={() => setQuestion(null)}
          onConfirm={() => apply({ type: 'changeOutcome', id: question.line.id, result: question.result })}
        />
      )}
      {question?.kind === 'remove' && (
        <ConfirmChange
          title="Remove This Course?"
          lead={`This takes the course out of your ${year} record.`}
          facts={[
            { term: 'Removing', value: `${question.line.course_code}: ${question.line.course_name}`, danger: true },
            { term: 'Year', value: `${year}, ${termLabels[question.line.term]}` },
            { term: 'Outcome', value: wordsFor(question.line.result) },
          ]}
          cancelLabel="Keep Course"
          confirmLabel="Remove Course"
          destructive
          onCancel={() => setQuestion(null)}
          onConfirm={() => apply({ type: 'remove', id: question.line.id })}
        />
      )}
    </div>
  )
}
