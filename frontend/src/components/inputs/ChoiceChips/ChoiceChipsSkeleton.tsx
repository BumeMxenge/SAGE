// A question's skeleton while the questions are on their way, laid out as ChoiceChips lays out the
// question: its words, its hint if it has one, and a row of chips. Each length is in characters.
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import styles from './ChoiceChips.module.css'

type ChoiceChipsSkeletonProps = { label: number; description?: number; chips: number[] }

export function ChoiceChipsSkeleton({ label, description, chips }: ChoiceChipsSkeletonProps) {
  return (
    <div className={styles.group}>
      <span className={styles.label}>
        <Skeleton variant="line" length={label} />
      </span>
      {description !== undefined && (
        <span className={styles.description}>
          <Skeleton variant="line" length={description} />
        </span>
      )}
      <span className={styles.chips}>
        {chips.map((length, index) => (
          // The chips never move, so their places name them
          <Skeleton key={index} variant="chip" length={length} />
        ))}
      </span>
    </div>
  )
}
