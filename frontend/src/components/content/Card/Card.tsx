// A flat card with a heading, such as an elective or a plan being compared. Its heading is an h3, or
// an h2 where the card sits straight under the page's h1, as the transcript's card does, so the
// page's headings stay in order. Pages that need a more specific card, like an elective card, build it
// from this one through its props.
import type { ReactNode } from 'react'
import styles from './Card.module.css'

type CardProps = { title: string; level?: 2 | 3; actions?: ReactNode; children?: ReactNode }

export function Card({ title, level = 3, actions, children }: CardProps) {
  const Heading = level === 2 ? 'h2' : 'h3'
  return (
    <article className={styles.card}>
      <header className={styles.header}>
        <Heading className={styles.title}>{title}</Heading>
        {actions}
      </header>
      {children}
    </article>
  )
}
