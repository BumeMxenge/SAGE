// One option of a SegmentedControl. The id is the key the control reports when it is chosen. With an
// icon it shows only the icon, as Calendar and Course List do when the sidebar and the assistant are
// both open, and the label still names it for screen readers.
import { ToggleButton } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import type { IconName } from '@/components/Icon/icons.ts'
import styles from './SegmentedControl.module.css'

type SegmentProps = { id: string; icon?: Exclude<IconName, 'favorite'>; children: string }

export function Segment({ id, icon, children }: SegmentProps) {
  return (
    <ToggleButton id={id} aria-label={icon && children} className={styles.segment}>
      {icon ? <Icon name={icon} /> : children}
    </ToggleButton>
  )
}
