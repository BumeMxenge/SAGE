// One action in a Menu. A destructive one, such as Sign Out, is red. In a section where one item is
// chosen, such as Appearance, the chosen item shows a tick.
import type { ReactNode } from 'react'
import { MenuItem as AriaMenuItem } from 'react-aria-components'
import { Icon, type IconName } from '@/components/Icon/Icon.tsx'
import styles from '@/components/Popover/Popover.module.css'

type MenuItemProps = {
  id: string
  icon?: Exclude<IconName, 'favorite'>
  isDestructive?: boolean
  onAction?: () => void
  children: ReactNode
}

export function MenuItem({ id, icon, isDestructive, onAction, children }: MenuItemProps) {
  return (
    <AriaMenuItem
      id={id}
      textValue={typeof children === 'string' ? children : id}
      onAction={onAction}
      className={`${styles.item} ${isDestructive ? styles.destructive : ''}`}
    >
      {({ isSelected }) => (
        <>
          <span className={styles.text}>
            {icon && <Icon name={icon} />}
            {children}
          </span>
          {isSelected && <Icon name="check" />}
        </>
      )}
    </AriaMenuItem>
  )
}
