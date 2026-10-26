// The top of a page in the app, holding its h1: a title and an optional subtitle, always left-aligned
// at the reading width, and the page's headline figure, if it has one, such as Course History's
// cumulative average, at the far end of the page. A blocking error page has none: its ErrorState holds
// the h1.
import type { ReactNode } from 'react'
import styles from './PageHeader.module.css'

// A sticky header stays at the top of the window as the page scrolls beneath it
type PageHeaderProps = { title: string; subtitle?: string; sticky?: boolean; figure?: ReactNode }

export function PageHeader({ title, subtitle, sticky = false, figure }: PageHeaderProps) {
  return (
    <header className={sticky ? `${styles.pageHeader} ${styles.sticky}` : styles.pageHeader}>
      <div className={styles.heading}>
        <h1 className={styles.title}>{title}</h1>
        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      </div>
      {figure && <div className={styles.figure}>{figure}</div>}
    </header>
  )
}
