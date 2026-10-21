// The list of options a Select opens, which a dialog can also show on its own, as the course picker
// does. Options are SelectItems. Inside a Select it takes the Select's choice; on its own, aria-label
// names it and onAction reports the option pressed.
import type { ReactNode } from 'react'
import { type Key, ListBox } from 'react-aria-components'
import listStyles from '@/components/overlays/Popover/Popover.module.css'
import styles from './OptionList.module.css'

type OptionListProps = { 'aria-label'?: string; onAction?: (key: Key) => void; children: ReactNode }

export function OptionList({ children, ...props }: OptionListProps) {
  return (
    <ListBox {...props} className={`${listStyles.list} ${styles.optionList}`}>
      {children}
    </ListBox>
  )
}
