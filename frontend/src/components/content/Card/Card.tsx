// A flat card with a heading, such as an elective or a plan being compared. Its heading is an h3, or
// an h2 where the card sits straight under the page's h1, as the transcript's card does, so the
// page's headings stay in order. A meta line, such as a file's size, sits right under the heading,
// with the actions centred beside the two. Pages that need a more specific card, like an elective
// card, build it from this one through its props.
import type { ReactNode } from 'react'
import styles from './Card.module.css'

type CardProps = { title: string; level?: 2 | 3; meta?: ReactNode; actions?: ReactNode; children?: ReactNode }

export function Card({ title, level = 3, meta, actions, children }: CardProps) {
  const Heading = level === 2 ? 'h2' : 'h3'
  return (
    <article className={styles.card}>
      <header className={styles.header} data-meta={meta !== undefined || undefined}>
        <div className={styles.heading}>
          <Heading className={styles.title}>{title}</Heading>
          {meta}
        </div>
        {actions}
      </header>
      {children}
    </article>
  )
}
