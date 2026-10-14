// What a region shows when it can't load or something blocked it: a title, a message and the action
// that gets past it. A screen reader announces it as soon as it appears. Which message and action go
// with which problem code comes with the app's error map.
import type { ReactNode } from 'react'
import { Icon } from '@/components/Icon/Icon.tsx'
import styles from './ErrorState.module.css'

type ErrorStateProps = { title: string; message: string; action?: ReactNode }

export function ErrorState({ title, message, action }: ErrorStateProps) {
  return (
    <div role="alert" className={styles.errorState}>
      <span aria-hidden="true" className={styles.tile}>
        <Icon name="error" />
      </span>
      <h2 className={styles.title}>{title}</h2>
      <p className={styles.message}>{message}</p>
      {action}
    </div>
  )
}
