// An elective card's skeleton, from the shared Card and the card's own styles: its name, its codes
// line, two lines of summary and its convener
import { Card } from '@/components/content/Card/Card.tsx'
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import styles from './ElectiveCard.module.css'

export function ElectiveCardSkeleton({ nameLength }: { nameLength: number }) {
  return (
    <Card
      title={<Skeleton variant="line" length={nameLength} />}
      meta={
        <p className={styles.meta}>
          <Skeleton variant="line" length={30} />
        </p>
      }
    >
      <p className={styles.summary}>
        <Skeleton variant="line" />
        <Skeleton variant="line" length={24} />
      </p>
      <p className={styles.conveners}>
        <Skeleton variant="line" length={18} />
      </p>
    </Card>
  )
}
