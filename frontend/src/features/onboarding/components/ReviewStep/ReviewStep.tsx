// The review: the course history read from the transcript, one year at a time, for the student to
// confirm. Their programme comes from the transcript, or they choose it. Notes that came with the
// reading show above. On the last year, once they tick that it reflects their record, Finish Setup
// sends the whole history in one request.
import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Button } from '@/components/actions/Button/Button.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { Checkbox } from '@/components/inputs/Checkbox/Checkbox.tsx'
import { Select } from '@/components/inputs/Select/Select.tsx'
import { SelectItem } from '@/components/inputs/Select/SelectItem.tsx'
import { YearTable } from '@/features/onboarding/components/YearTable/YearTable.tsx'
import { setupOf, startReview } from '@/features/onboarding/review.ts'
import { client, dataOf } from '@/lib/api.ts'
import type { components } from '@/lib/api-types.ts'
import { queries } from '@/lib/queryKeys.ts'
import styles from './ReviewStep.module.css'

type Transcript = components['schemas']['Transcript']

// A title for each note the reading can send, so a new kind of note fails the build until it has one
const warningTitles: Record<components['schemas']['TranscriptWarning']['code'], string> = {
  term_gpa_mismatch: "A Term Average Doesn't Match",
  recent_year_missing: 'No Courses Last Year',
  results_pending: "Some Results Aren't Out Yet",
}

const courses = (count: number) => `${count} ${count === 1 ? 'course' : 'courses'}`

type ReviewStepProps = { transcript: Transcript; onSaved: () => Promise<void> }

export function ReviewStep({ transcript, onSaved }: ReviewStepProps) {
  const [review, setReview] = useState(() => startReview(transcript))
  const [yearIndex, setYearIndex] = useState(0)
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
  const outcomes = new Map(catalogue.data?.symbols.map((symbol) => [symbol.symbol, symbol.label]))
  const caption = `${year} · Year ${yearIndex + 1} of ${years.length}`
  const programme = transcript.curriculum_options.length === 1 ? transcript.curriculum_options[0] : null

  // Finish Setup needs the box ticked, a programme, and at least one course, as the API can't save an
  // empty history. The box sits just above it; the other two say why it waits.
  const canFinish = confirmed && review.curriculum !== null && review.lines.length > 0 && !saving.isPending
  function finishHint(): string | null {
    if (!isLast) return null
    if (review.lines.length === 0) return 'Add at least one course to finish.'
    if (!review.curriculum) return 'Choose your programme to finish.'
    return null
  }
  const hint = finishHint()

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
                if (code !== null) setReview({ ...review, curriculum: String(code) })
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
      {/* Each year takes focus as it opens, so a screen reader hears which year it is, and the page
          shows it from the top */}
      <section
        key={year}
        ref={(section) => {
          section?.focus({ preventScroll: true })
          scrollTo(0, 0)
        }}
        tabIndex={-1}
        aria-label={caption}
        className={styles.year}
      >
        <p className={styles.summary}>
          {courses(lines.length)} · {credits} credits
        </p>
        <YearTable caption={caption} lines={lines} outcomes={outcomes} />
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
            <Button onPress={() => setYearIndex(yearIndex + 1)}>Confirm {year}</Button>
          )}
        </div>
      </div>
    </div>
  )
}
