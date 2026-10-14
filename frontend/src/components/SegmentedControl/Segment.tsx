// One option of a SegmentedControl. The id is the key the control reports when it is chosen.
import type { ReactNode } from 'react'
import { ToggleButton } from 'react-aria-components'
import styles from './SegmentedControl.module.css'

export function Segment({ id, children }: { id: string; children: ReactNode }) {
  return (
    <ToggleButton id={id} className={styles.segment}>
      {children}
    </ToggleButton>
  )
}
