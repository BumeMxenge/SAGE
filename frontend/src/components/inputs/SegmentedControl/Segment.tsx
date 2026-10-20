// One option of a SegmentedControl. The id is the key the control reports when it is chosen. With an
// icon it shows only the icon, as Calendar and Course List do when the sidebar and the assistant are
// both open, and the label still names it for screen readers.
import { ToggleButton } from 'react-aria-components'
import { Icon, type PlainIconName } from '@/components/brand/Icon/Icon.tsx'
import styles from './SegmentedControl.module.css'

type SegmentProps = { id: string; icon?: PlainIconName; children: string }

export function Segment({ id, icon, children }: SegmentProps) {
  return (
    <ToggleButton id={id} aria-label={icon && children} className={styles.segment}>
      {icon ? <Icon name={icon} /> : children}
    </ToggleButton>
  )
}
