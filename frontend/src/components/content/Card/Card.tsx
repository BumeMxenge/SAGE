// A flat card with a heading, such as an elective or a plan being compared. Pages that need a more
// specific card, like an elective card, build it from this one through its props.
import type { ReactNode } from 'react'
import styles from './Card.module.css'

type CardProps = { title: string; actions?: ReactNode; children?: ReactNode }

export function Card({ title, actions, children }: CardProps) {
  return (
    <article className={styles.card}>
      <header className={styles.header}>
        <h3 className={styles.title}>{title}</h3>
        {actions}
      </header>
      {children}
    </article>
  )
}
