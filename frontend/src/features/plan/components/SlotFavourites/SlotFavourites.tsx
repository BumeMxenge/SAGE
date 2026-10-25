// Her favourites that fit a plan, on its slot card, each a button that previews it in the plan's week.
// They come from Explore Electives' read, where the API says which plans each offering fits, so a
// heart changed there shows here too. A course offered in two terms that both fit has a button for
// each, naming its term. While the read is on its way, skeletons hold the buttons' place, and if it
// fails, a note says so with Try Again. With no favourite that fits, nothing shows.
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { Button } from '@/components/actions/Button/Button.tsx'
import { Arrival } from '@/components/feedback/Arrival/Arrival.tsx'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import type { components } from '@/lib/api-types.ts'
import { termLabels } from '@/lib/copy.ts'
import { actionLabels, explain } from '@/lib/errors.ts'
import { previewPath } from '@/lib/planAddress.ts'
import { queries } from '@/lib/queryKeys.ts'
import { loadingFavourites, previewCourse, previewCourseIn } from '../../copy.ts'
import styles from './SlotFavourites.module.css'

type Tab = components['schemas']['Tab']
type Offering = components['schemas']['Offering']

// Each hearted offering that fits the plan, once, though a course can sit on two tabs, with the words
// on its button
function favouritesIn(tabs: Tab[], planId: string): { offering: Offering; label: string }[] {
  const found = new Map<string, { offering: Offering; label: string }>()
  for (const card of tabs.flatMap((tab) => tab.courses)) {
    const fitting = card.offerings.filter((offering) => offering.hearted && offering.plans.includes(planId))
    for (const offering of fitting) {
      const label = fitting.length > 1 ? previewCourseIn(card.name, termLabels[offering.term]) : previewCourse(card.name)
      found.set(offering.code, { offering, label })
    }
  }
  return [...found.values()]
}

export function SlotFavourites({ planId }: { planId: string }) {
  const electives = useQuery(queries.electives())
  const navigate = useNavigate()

  if (electives.isError) {
    const { title, message } = explain(electives.error)
    return (
      <ErrorState variant="inline" tone="warning" icon="warning" title={title} message={message}>
        <Button variant="secondary" onPress={() => void electives.refetch()}>
          {actionLabels.retry}
        </Button>
      </ErrorState>
    )
  }
  return (
    <Arrival
      data={electives.data}
      waiting={electives.isPending}
      skeleton={
        <div aria-hidden="true" className={styles.favourites}>
          <Skeleton variant="control" length={18} />
          <Skeleton variant="control" length={24} />
        </div>
      }
      status={loadingFavourites}
    >
      {({ tabs }) => {
        const favourites = favouritesIn(tabs, planId)
        return (
          favourites.length > 0 && (
            <div className={styles.favourites}>
              {favourites.map(({ offering, label }) => (
                <Button key={offering.code} variant="secondary" onPress={() => void navigate(previewPath(planId, offering.code, offering.term))}>
                  {label}
                </Button>
              ))}
            </div>
          )
        )
      }}
    </Arrival>
  )
}
