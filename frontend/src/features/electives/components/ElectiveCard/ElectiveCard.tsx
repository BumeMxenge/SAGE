// One course on Explore Electives, built from the shared Card: its name, its codes, when it runs and
// its credits, its summary and conveners, and at its foot the API's note, if it has one, after the
// warning sign. Its one heart hearts the course. The heart shows when she can heart the course, and
// on a course she hearted that she no longer can, so she can still take the heart away. A course she
// can't heart is greyed, and its note says why. On the page filtered to a plan, its previews in that
// plan sit at its foot.
import type { ReactNode } from 'react'
import { IconButton } from '@/components/actions/IconButton/IconButton.tsx'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import { Card } from '@/components/content/Card/Card.tsx'
import type { components } from '@/lib/api-types.ts'
import { codesOf, convenersOf, termsOf } from '../../cards.ts'
import styles from './ElectiveCard.module.css'

type Elective = components['schemas']['Elective']

type ElectiveCardProps = { card: Elective; onHeartChange: (heart: boolean) => void; previews?: ReactNode }

export function ElectiveCard({ card, onHeartChange, previews }: ElectiveCardProps) {
  const conveners = convenersOf(card)
  return (
    <Card
      title={card.name}
      unavailable={!card.can_heart}
      meta={
        <p className={styles.meta}>
          <span className={styles.codes}>{codesOf(card)}</span> · {termsOf(card)} · {card.credits} credits
        </p>
      }
      actions={
        (card.can_heart || card.hearted) && (
          <IconButton icon="favorite" label={`Favourite ${card.name}`} isSelected={card.hearted} onChange={onHeartChange} />
        )
      }
    >
      {card.summary && <p className={styles.summary}>{card.summary}</p>}
      {conveners && <p className={styles.conveners}>{conveners}</p>}
      {card.note && (
        <p className={styles.note}>
          <Icon name="warning" />
          {card.note}
        </p>
      )}
      {previews && <div className={styles.previews}>{previews}</div>}
    </Card>
  )
}
