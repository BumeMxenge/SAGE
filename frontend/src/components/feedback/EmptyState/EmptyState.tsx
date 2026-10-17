// What a region shows when there is nothing in it yet: a title, a message and the action that fills it.
import { type ReactNode, useId } from 'react'
import styles from './EmptyState.module.css'

type EmptyStateProps = { title: string; message: string; action?: ReactNode }

export function EmptyState({ title, message, action }: EmptyStateProps) {
  const headingId = useId()
  return (
    <section aria-labelledby={headingId} className={styles.emptyState}>
      <h2 id={headingId} className={styles.title}>
        {title}
      </h2>
      <p className={styles.message}>{message}</p>
      {action}
    </section>
  )
}
