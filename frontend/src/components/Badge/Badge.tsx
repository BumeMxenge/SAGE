// A short label such as a course code or a status. It always holds words, so colour is never the only
// thing that tells one badge from another.
import type { ReactNode } from 'react'
import styles from './Badge.module.css'

type BadgeProps = { tone?: 'neutral' | 'accent' | 'warning' | 'danger'; children: ReactNode }

export function Badge({ tone = 'neutral', children }: BadgeProps) {
  return <span className={`${styles.badge} ${styles[tone]}`}>{children}</span>
}
