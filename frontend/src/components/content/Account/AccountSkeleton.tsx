// The account's skeleton while it is looked up, laid out as Account is: the avatar beside a line for
// the name and a shorter one for the second line
import { Skeleton } from '@/components/feedback/Skeleton/Skeleton.tsx'
import styles from './Account.module.css'

export function AccountSkeleton() {
  return (
    <span className={styles.account}>
      <Skeleton variant="avatar" />
      <span className={styles.text}>
        <span className={styles.name}>
          <Skeleton variant="line" length={12} />
        </span>
        <span className={styles.detail}>
          <Skeleton variant="line" length={18} />
        </span>
      </span>
    </span>
  )
}
