// Explore Electives' tabs, one for each category the API sends, as React Aria's tabs: the arrow keys
// move between them, and only the open tab's courses are on the page, under its heading and the line
// that says what it holds, in a grid of cards. The page keeps the open tab in its address.
import type { ReactNode } from 'react'
import { Tab, TabList, TabPanel, Tabs } from 'react-aria-components'
import type { components } from '@/lib/api-types.ts'
import { tabWords } from '../../copy.ts'
import styles from './CategoryTabs.module.css'

type CourseTab = components['schemas']['Tab']

type CategoryTabsProps = {
  tabs: CourseTab[]
  selected: string
  onSelect: (tab: string) => void
  children: (tab: CourseTab) => ReactNode
}

export function CategoryTabs({ tabs, selected, onSelect, children }: CategoryTabsProps) {
  return (
    <Tabs selectedKey={selected} onSelectionChange={(key) => onSelect(String(key))} className={styles.tabs}>
      <TabList aria-label="Categories" className={styles.list}>
        {tabs.map((tab) => (
          <Tab key={tab.key} id={tab.key} className={styles.tab}>
            {tabWords[tab.key].label}
          </Tab>
        ))}
      </TabList>
      {tabs.map((tab) => (
        <TabPanel key={tab.key} id={tab.key} className={styles.panel}>
          <h2 className={styles.heading}>{tabWords[tab.key].label}</h2>
          <p className={styles.sub}>{tabWords[tab.key].sub}</p>
          <div className={styles.grid}>{children(tab)}</div>
        </TabPanel>
      ))}
    </Tabs>
  )
}
