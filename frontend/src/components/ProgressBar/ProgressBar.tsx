// How far a task has got, such as reading a transcript. With a value it fills to that percentage.
// Without one it slides back and forth. The label always shows, so reduced motion loses nothing.
import { Label, ProgressBar as AriaProgressBar } from 'react-aria-components'
import styles from './ProgressBar.module.css'

type ProgressBarProps = { label: string; value?: number }

export function ProgressBar({ label, value }: ProgressBarProps) {
  return (
    <AriaProgressBar className={styles.progressBar} value={value} isIndeterminate={value === undefined}>
      {({ percentage, valueText }) => (
        <>
          <div className={styles.text}>
            <Label>{label}</Label>
            {value !== undefined && <span>{valueText}</span>}
          </div>
          <div className={styles.track}>
            <div className={styles.fill} style={{ '--progress': `${percentage}%` }} />
          </div>
        </>
      )}
    </AriaProgressBar>
  )
}
