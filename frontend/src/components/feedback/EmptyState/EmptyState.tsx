// What a region shows when there is nothing in it yet: an optional picture, such as the calendar over
// an empty term, a title, a message and the action that fills it.
import { type ReactNode, useId } from 'react'
import { Icon, type PlainIconName } from '@/components/brand/Icon/Icon.tsx'
import styles from './EmptyState.module.css'

type EmptyStateProps = { title: string; message: string; icon?: PlainIconName; action?: ReactNode }

export function EmptyState({ title, message, icon, action }: EmptyStateProps) {
  const headingId = useId()
  return (
    <section aria-labelledby={headingId} className={styles.emptyState}>
      {icon && (
        <span aria-hidden="true" className={styles.icon}>
          <Icon name={icon} />
        </span>
      )}
      <h2 id={headingId} className={styles.title}>
        {title}
      </h2>
      <p className={styles.message}>{message}</p>
      {action}
    </section>
  )
}
