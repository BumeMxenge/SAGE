// One of a plan's complementary slots, as a dashed card under the plan's term: what the slot needs, how
// many approved courses fit the plan's timetable and how many of those need a check, and a link to
// Explore Electives showing only those. When none fits, the engine's own words say so, and there is
// nothing to browse. A line asks for a course of its credits, and a 576-credit place names the course
// it takes the place of. The numbers are the API's, counted as Explore Electives' cards are.
import { Link } from 'react-aria-components'
import { Card } from '@/components/content/Card/Card.tsx'
import type { components } from '@/lib/api-types.ts'
import { electivesPath } from '@/lib/electivesAddress.ts'
import { browse, fitting, inPlaceOf, lineNeeds, placeNeeds, slotTitle } from '../../copy.ts'
import styles from './SlotCard.module.css'

type Slot = components['schemas']['Slot']

// Its heading sits under the page's h1, or under a compare panel's h2
type SlotCardProps = { slot: Slot; planId: string; level: 2 | 3 }

export function SlotCard({ slot, planId, level }: SlotCardProps) {
  const { replaces } = slot
  return (
    <Card title={replaces === null ? slotTitle : inPlaceOf(replaces)} level={level} dashed>
      {slot.fit_count === 0 ? (
        <p className={styles.line}>{slot.message}</p>
      ) : (
        <>
          <p className={styles.line}>{replaces === null ? lineNeeds(slot.credits) : placeNeeds(slot.credits)}</p>
          <p className={styles.line}>{fitting(slot.fit_count, slot.check_count)}</p>
          <Link href={electivesPath({ planId, tab: null })} className={styles.browse}>
            {browse(slot.fit_count)}
          </Link>
        </>
      )}
    </Card>
  )
}
