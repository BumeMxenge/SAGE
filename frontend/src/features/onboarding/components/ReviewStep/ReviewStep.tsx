// The review: the course history read from the transcript, one year at a time, for the student to
// check, correct and confirm, on the programme they settled when they uploaded it. Notes that came
// with the reading show above. In edit mode they can change an outcome, remove a course or add one
// from the catalogue, each after a question that says what will change. On the last year, once they
// tick that it reflects their record, Finish Setup sends the whole history in one request.
import { useMutation, useQuery } from '@tanstack/react-query'
import { useCallback, useReducer, useState } from 'react'
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
import { watchEnd } from '@/features/onboarding/watchEnd.ts'
import {
  isOutcome,
  type Outcome,
  offeredOutcomes,
  outcomes,
  type ReviewAction,
  type ReviewLine,
  reviewReducer,
  setupOf,
  startReview,
  wordFor,
} from '@/features/onboarding/review.ts'
import { client, dataOf } from '@/lib/api.ts'
import type { components } from '@/lib/api-types.ts'
import { termLabels } from '@/lib/copy.ts'
import { queries } from '@/lib/queryKeys.ts'
import styles from './ReviewStep.module.css'

type Transcript = components['schemas']['Transcript']
type Course = components['schemas']['Course']
type TranscriptWarning = components['schemas']['TranscriptWarning']

// The notes the review shows. Pending results aren't one, as each such course already says In progress.
type ShownWarning = TranscriptWarning & { code: Exclude<TranscriptWarning['code'], 'results_pending'> }
const isShown = (warning: TranscriptWarning): warning is ShownWarning => warning.code !== 'results_pending'

// A title for each note shown, so a new kind of note fails the build until it has one
const warningTitles: Record<ShownWarning['code'], string> = {
  term_gpa_mismatch: "A Term Average Doesn't Match",
  recent_year_missing: 'No Courses Last Year',
}

// The question open over the review, if any: picking a course, or confirming one change
type Question =
  | { kind: 'pick' }
  | { kind: 'add'; course: Course; outcome: Outcome | null }
  | { kind: 'change'; line: ReviewLine; outcome: Outcome }
  | { kind: 'remove'; line: ReviewLine }

const courses = (count: number) => `${count} ${count === 1 ? 'course' : 'courses'}`

type ReviewStepProps = { transcript: Transcript; curriculum: string; onSaved: () => Promise<void> }

export function ReviewStep({ transcript, curriculum, onSaved }: ReviewStepProps) {
  const [review, dispatch] = useReducer(reviewReducer, transcript, startReview)
  const [yearIndex, setYearIndex] = useState(0)
  const [editing, setEditing] = useState(false)
  const [question, setQuestion] = useState<Question | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  // The years, by their place in the list, whose table the student has seen to its end, or whose rows
  // all fit. A year is read once, and stays read if they go back to it, as in the prototype.
  const [read, setRead] = useState<ReadonlySet<number>>(() => new Set())
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
  const isRead = read.has(yearIndex)
  // Each year's table takes focus as it opens, and counts as read once scrolled to its end. One
  // function per year, so React calls it only as the year's table mounts.
  const yearBox = useCallback(
    (box: HTMLElement | null) => {
      focusOnOpen(box)
      if (!box) return
      return watchEnd(box, () => setRead((places) => (places.has(yearIndex) ? places : new Set([...places, yearIndex]))))
    },
    [yearIndex],
  )
  // Each result symbol's outcome, from the catalogue
  const outcomeOf = new Map((catalogue.data?.symbols ?? []).map(({ symbol, outcome }) => [symbol, outcome]))

  function apply(action: ReviewAction) {
    dispatch(action)
    setQuestion(null)
  }

  // Moving on waits for the student to finish editing and to read the year to its end. Finish Setup
  // also needs the box ticked and at least one course, as the API can't save an empty history. The box
  // sits just above it; the rest say why it waits.
  const canMoveOn = !editing && isRead
  const canFinish = canMoveOn && confirmed && review.lines.length > 0 && !saving.isPending
  function nextHint(): string | null {
    if (editing) return 'Finish editing to continue.'
    if (!isRead) return 'Scroll to the end of the year to continue.'
    if (isLast && review.lines.length === 0) return 'Add at least one course to finish.'
    return null
  }
  const hint = nextHint()

  function finish() {
    saving.mutate(setupOf(curriculum, review.lines))
  }

  return (
    <div className={styles.review}>
      <PageHeader
        title="Review Your Course History"
        subtitle={`We pulled ${courses(transcript.lines.length)} out of your transcript. Confirm one year at a time. SAGE checks every prerequisite against this history, so anything wrong here follows you through registration.`}
      />
      {transcript.warnings.filter(isShown).map((warning) => (
        <ErrorState
          key={warning.code}
          variant="inline"
          tone="warning"
          icon="info"
          title={warningTitles[warning.code]}
          message={warning.message}
        />
      ))}
      <div key={year} className={styles.year}>
        <div className={styles.tools}>
          <p className={styles.summary}>
            {courses(lines.length)} · {credits} credits
          </p>
          {editing ? (
            <>
              <Button variant="quiet" icon="add" onPress={() => setQuestion({ kind: 'pick' })}>
                Add a Course
              </Button>
              <Button variant="dark" onPress={() => setEditing(false)}>
                Done Editing
              </Button>
            </>
          ) : (
            <Button variant="secondary" onPress={() => setEditing(true)}>
              Edit Courses
            </Button>
          )}
        </div>
        {/* Each year's table takes focus as it opens, so a screen reader hears which year it is, and the
            arrow keys can scroll it */}
        <YearTable
          ref={yearBox}
          caption={caption}
          lines={lines}
          outcomeOf={outcomeOf}
          editing={editing}
          onChangeOutcome={(line, outcome) => setQuestion({ kind: 'change', line, outcome })}
          onRemove={(line) => setQuestion({ kind: 'remove', line })}
        />
      </div>
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
            <Button isDisabled={!canMoveOn} onPress={() => setYearIndex(yearIndex + 1)}>
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
          onPick={(course) => setQuestion({ kind: 'add', course, outcome: null })}
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
                  variant="plain"
                  label={`Outcome for ${question.course.code}`}
                  placeholder="Set the outcome for this course"
                  selectedKey={question.outcome}
                  onSelectionChange={(outcome) => {
                    if (isOutcome(outcome)) setQuestion({ ...question, outcome })
                  }}
                >
                  {offeredOutcomes.map((outcome) => (
                    <SelectItem key={outcome} id={outcome}>
                      {outcomes[outcome].word}
                    </SelectItem>
                  ))}
                </Select>
              ),
            },
          ]}
          cancelLabel="Back to List"
          confirmLabel="Add Course"
          isConfirmDisabled={question.outcome === null}
          onCancel={() => setQuestion({ kind: 'pick' })}
          onConfirm={() => {
            if (question.outcome !== null) apply({ type: 'add', year, course: question.course, outcome: question.outcome })
          }}
        />
      )}
      {question?.kind === 'change' && (
        <ConfirmChange
          title="Change This Outcome?"
          lead="Outcomes drive prerequisite checks."
          facts={[
            { term: 'Course', value: `${question.line.course_code}: ${question.line.course_name}` },
            { term: 'From', value: wordFor(question.line.result, outcomeOf) },
            { term: 'To', value: outcomes[question.outcome].word },
          ]}
          cancelLabel="Keep Outcome"
          confirmLabel="Change Outcome"
          onCancel={() => setQuestion(null)}
          onConfirm={() => apply({ type: 'changeOutcome', id: question.line.id, outcome: question.outcome })}
        />
      )}
      {question?.kind === 'remove' && (
        <ConfirmChange
          title="Remove This Course?"
          lead={`This takes the course out of your ${year} record.`}
          facts={[
            { term: 'Removing', value: `${question.line.course_code}: ${question.line.course_name}`, danger: true },
            { term: 'Year', value: `${year}, ${termLabels[question.line.term]}` },
            { term: 'Outcome', value: wordFor(question.line.result, outcomeOf) },
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
