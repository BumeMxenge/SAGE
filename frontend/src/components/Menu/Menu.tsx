// A menu of actions that opens from a button. The trigger is a Button or IconButton. The label names
// the menu for screen readers.
import type { ReactElement, ReactNode } from 'react'
import { Menu as AriaMenu, MenuTrigger } from 'react-aria-components'
import { Popover } from '@/components/Popover/Popover.tsx'
import styles from '@/components/Popover/Popover.module.css'

type MenuProps = { label: string; trigger: ReactElement; children: ReactNode }

export function Menu({ label, trigger, children }: MenuProps) {
  return (
    <MenuTrigger>
      {trigger}
      <Popover>
        <AriaMenu aria-label={label} className={styles.list}>
          {children}
        </AriaMenu>
      </Popover>
    </MenuTrigger>
  )
}
