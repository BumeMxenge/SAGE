// Three pulsing dots beside a line such as "SAGE is replying". The words are always there, and the
// status role makes a screen reader announce them. Under reduced motion the dots stand still.
import styles from './TypingIndicator.module.css'

export function TypingIndicator({ label }: { label: string }) {
  return (
    <output className={styles.typingIndicator}>
      <span aria-hidden="true" className={styles.dots}>
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.dot} />
      </span>
      {label}
    </output>
  )
}
