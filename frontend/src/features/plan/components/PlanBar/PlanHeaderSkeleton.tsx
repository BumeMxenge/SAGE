// The plan header's skeleton while the plan is on its way, as loading case 01 draws it: the plan
// switcher, the plan's credits and Compare, each in its place
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import styles from './PlanBar.module.css'

export function PlanHeaderSkeleton() {
  return (
    <>
      <Skeleton variant="control" length={30} />
      <span className={styles.credits}>
        <Skeleton variant="line" length={9} />
      </span>
      <Skeleton variant="control" length={13} />
    </>
  )
}
