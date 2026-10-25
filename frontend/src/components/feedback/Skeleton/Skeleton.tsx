// A grey placeholder where content is loading, in the shape of what will arrive: a line of text, a
// control such as a button or the plan switcher, a choice chip, the account's avatar, or a block that
// fills the place it is given, such as a meeting in a plan's week. A line sits in the text around it,
// as tall as that text's line, so a row holding one is as tall as the row that replaces it. A line,
// control or chip is as long as the given number of characters of the text around it, and otherwise
// takes its parent's width. Screen readers skip it, so the page that holds it says what is loading in
// a status line.
import styles from './Skeleton.module.css'

type SkeletonProps = { variant: 'line' | 'control' | 'chip' | 'avatar' | 'block'; length?: number }

export function Skeleton({ variant, length }: SkeletonProps) {
  return (
    <span
      aria-hidden="true"
      className={`${styles.skeleton} ${styles[variant]}`}
      data-length={length !== undefined || undefined}
      style={{ '--length': length }}
    />
  )
}
