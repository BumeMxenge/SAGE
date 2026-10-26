// What a region shows when there is nothing in it yet: an optional picture, such as the calendar over
// an empty term, a title, a message and the action that fills it. Its title is an h2, or an h3 inside
// a region with an h2 of its own, such as a compare panel.
import { type ReactNode, useId } from 'react'
import { Icon, type PlainIconName } from '@/components/brand/Icon/Icon.tsx'
import styles from './EmptyState.module.css'

type EmptyStateProps = { title: string; message: string; level?: 2 | 3; icon?: PlainIconName; action?: ReactNode }

export function EmptyState({ title, message, level = 2, icon, action }: EmptyStateProps) {
  const headingId = useId()
  const Heading = level === 2 ? 'h2' : 'h3'
  return (
    <section aria-labelledby={headingId} className={styles.emptyState}>
      {icon && (
        <span aria-hidden="true" className={styles.icon}>
          <Icon name={icon} />
        </span>
      )}
      <Heading id={headingId} className={styles.title}>
        {title}
      </Heading>
      <p className={styles.message}>{message}</p>
      {action}
    </section>
  )
}
