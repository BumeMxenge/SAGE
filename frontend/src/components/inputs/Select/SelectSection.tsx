// A titled group of a Select's options, such as the plans the questionnaire hid, below the rest. A
// screen reader hears the title as the group's name.
import type { ReactNode } from 'react'
import { Header, ListBoxSection } from 'react-aria-components'
import styles from '@/components/overlays/Popover/Popover.module.css'

export function SelectSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <ListBoxSection>
      <Header className={styles.header}>{title}</Header>
      {children}
    </ListBoxSection>
  )
}
