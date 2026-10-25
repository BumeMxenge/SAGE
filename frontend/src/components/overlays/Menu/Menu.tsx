// A menu of actions that opens from a button. The trigger is a Button or IconButton. The label names
// the menu for screen readers. A header, such as the account menu's note of who is signed in, sits
// above the items behind a line. With nothing to list, the empty text says so, as chat history does
// before a plan has a chat. onOpenChange hears the menu open and close, as the sidebar's rail does to
// open the sidebar with it.
import type { ReactElement, ReactNode } from 'react'
import { Menu as AriaMenu, MenuTrigger } from 'react-aria-components'
import { Popover } from '@/components/overlays/Popover/Popover.tsx'
import listStyles from '@/styles/list.module.css'
import styles from './Menu.module.css'

type MenuProps = {
  label: string
  trigger: ReactElement
  header?: ReactNode
  empty?: string
  onOpenChange?: (isOpen: boolean) => void
  children: ReactNode
}

export function Menu({ label, trigger, header, empty, onOpenChange, children }: MenuProps) {
  return (
    <MenuTrigger onOpenChange={onOpenChange}>
      {trigger}
      {/* 12 px from its button, so the account menu clears the line above the account, as the
          prototype draws it */}
      <Popover offset={12}>
        {header && <div className={styles.header}>{header}</div>}
        {/* React Aria wraps the empty text in a menu item, so the menu still holds one */}
        <AriaMenu
          aria-label={label}
          renderEmptyState={empty === undefined ? undefined : () => <p className={styles.empty}>{empty}</p>}
          className={`${listStyles.list} ${styles.list}`}
        >
          {children}
        </AriaMenu>
      </Popover>
    </MenuTrigger>
  )
}
