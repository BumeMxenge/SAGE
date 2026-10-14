// A group of menu items. Give it selectionMode="single" and the chosen key for a choice, such as
// Match System, Light or Dark.
import type { ReactNode } from 'react'
import { Header, MenuSection as AriaMenuSection, type MenuSectionProps } from 'react-aria-components'
import styles from '@/components/Popover/Popover.module.css'

type Props = Pick<MenuSectionProps<object>, 'selectionMode' | 'selectedKeys' | 'onSelectionChange'> & {
  title?: string
  children: ReactNode
}

export function MenuSection({ title, children, ...props }: Props) {
  return (
    <AriaMenuSection {...props}>
      {title && <Header className={styles.header}>{title}</Header>}
      {children}
    </AriaMenuSection>
  )
}
