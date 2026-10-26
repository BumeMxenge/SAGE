// A flat card with a heading, such as an elective or a plan being compared. Its heading is an h3, or
// an h2 where the card sits straight under the page's h1, as the transcript's card does, so the
// page's headings stay in order. A meta line, such as a file's size, sits right under the heading,
// with the actions centred beside the two. Pages that need a more specific card, like an elective
// card, build it from this one through its props. While a page's read is on its way, a skeleton
// can stand in its title. An unavailable card, such as an elective she can't take, has its frame and
// title greyed, and the card says why in its own words, so the grey isn't all that marks it. A dashed
// card stands for something still to choose, such as a plan's complementary slot.
import type { ReactNode } from 'react'
import styles from './Card.module.css'

type CardProps = {
  title: ReactNode
  level?: 2 | 3
  meta?: ReactNode
  actions?: ReactNode
  unavailable?: boolean
  dashed?: boolean
  children?: ReactNode
}

export function Card({ title, level = 3, meta, actions, unavailable = false, dashed = false, children }: CardProps) {
  const Heading = level === 2 ? 'h2' : 'h3'
  return (
    <article className={styles.card} data-unavailable={unavailable || undefined} data-dashed={dashed || undefined}>
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
