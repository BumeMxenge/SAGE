// One labelled part of the review page: a heading, one line saying what it shows, and the samples.
import { type ReactNode, useId } from 'react'
import styles from './DesignSystem.module.css'

export function Section({ title, intro, children }: { title: string; intro: string; children: ReactNode }) {
  const headingId = useId()
  return (
    <section aria-labelledby={headingId} className={styles.section}>
      <h2 id={headingId} className={styles.heading}>
        {title}
      </h2>
      <p className={styles.intro}>{intro}</p>
      {children}
    </section>
  )
}
