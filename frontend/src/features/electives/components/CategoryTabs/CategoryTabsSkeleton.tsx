// The tabs' skeleton while Explore Electives' courses are on their way, as loading case 04 draws it:
// a row of tabs, a tab's heading and the line under it, and a grid of cards, each in the place and
// size of what replaces it, from the tabs' own styles
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import { ElectiveCardSkeleton } from '../ElectiveCard/ElectiveCardSkeleton.tsx'
import styles from './CategoryTabs.module.css'

// Each tab's label and each card's name, in characters, varied as case 04 varies them
const tabLengths = [22, 24, 18, 28, 20, 16]
const nameLengths = [16, 22, 12, 19, 25, 14]

export function CategoryTabsSkeleton() {
  return (
    <div aria-hidden="true" className={styles.tabs}>
      <div className={styles.list}>
        {tabLengths.map((length) => (
          <span key={length} className={styles.tab}>
            <Skeleton variant="line" length={length} />
          </span>
        ))}
      </div>
      <div className={styles.panel}>
        <p className={styles.heading}>
          <Skeleton variant="line" length={20} />
        </p>
        <p className={styles.sub}>
          <Skeleton variant="line" length={40} />
        </p>
        <div className={styles.grid}>
          {nameLengths.map((length) => (
            <ElectiveCardSkeleton key={length} nameLength={length} />
          ))}
        </div>
      </div>
    </div>
  )
}
