// A titled group of SelectItems, such as the plans a student's answers hid.
import type { ReactNode } from 'react'
import { Header, ListBoxSection } from 'react-aria-components'
import styles from '@/components/Popover/Popover.module.css'

export function SelectSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <ListBoxSection>
      <Header className={styles.header}>{title}</Header>
      {children}
    </ListBoxSection>
  )
}
