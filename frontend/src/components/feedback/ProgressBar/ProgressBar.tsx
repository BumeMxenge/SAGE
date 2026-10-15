// How far a task has got, such as reading a transcript: a label, the percentage, and a bar that fills.
import { Label, ProgressBar as AriaProgressBar } from 'react-aria-components'
import styles from './ProgressBar.module.css'

export function ProgressBar({ label, value }: { label: string; value: number }) {
  return (
    <AriaProgressBar className={styles.progressBar} value={value}>
      {({ percentage, valueText }) => (
        <>
          <div className={styles.text}>
            <Label>{label}</Label>
            <span>{valueText}</span>
          </div>
          <div className={styles.track}>
            <div className={styles.fill} style={{ '--progress': `${percentage}%` }} />
          </div>
        </>
      )}
    </AriaProgressBar>
  )
}
