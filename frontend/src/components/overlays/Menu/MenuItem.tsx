// One action in a Menu. A destructive one, such as Sign Out, is red. In a section where one item is
// chosen, such as Appearance, the chosen item is semibold as well as filled. An icon sits before the
// words, as each chat in Chat History has.
import type { ReactNode } from 'react'
import { MenuItem as AriaMenuItem } from 'react-aria-components'
import { Icon, type PlainIconName } from '@/components/brand/Icon/Icon.tsx'
import styles from '@/components/overlays/Popover/Popover.module.css'
import itemStyles from './MenuItem.module.css'

type MenuItemProps = {
  id: string
  icon?: PlainIconName
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
      className={`${styles.item} ${itemStyles.item} ${isDestructive ? styles.destructive : ''}`}
    >
      {icon && <Icon name={icon} />}
      <span className={styles.text}>{children}</span>
    </AriaMenuItem>
  )
}
