// A grey placeholder where content is loading. The shape matches what will arrive: a line of text,
// a title, or a block that fills its parent. Screen readers skip it, so the page that holds it
// should say it is loading, for example with a ProgressBar or a status line.
import styles from './Skeleton.module.css'

export function Skeleton({ variant }: { variant: 'line' | 'title' | 'block' }) {
  return <span aria-hidden="true" className={`${styles.skeleton} ${styles[variant]}`} />
}
