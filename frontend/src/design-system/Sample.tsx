// One sample on the review page, with a caption saying which state it shows.
import type { ReactNode } from 'react'
import styles from './DesignSystem.module.css'

export function Sample({ label, children }: { label: string; children: ReactNode }) {
  return (
    <figure className={styles.sample}>
      <div className={styles.stage}>{children}</div>
      <figcaption className={styles.caption}>{label}</figcaption>
    </figure>
  )
}
