// The top of a page in the app, holding its h1: a title and an optional subtitle, always left-aligned
// at the reading width, and either actions or the page's headline figure, such as Course History's
// cumulative average, at the far end of the page. A blocking error page has none: its ErrorState holds
// the h1.
import type { ReactNode } from 'react'
import styles from './PageHeader.module.css'

// The end of the title's row has room for actions or a figure, not both. A sticky header stays at the
// top of the window as the page scrolls beneath it.
type PageHeaderProps = { title: string; subtitle?: string; sticky?: boolean } & (
  | { actions?: ReactNode; figure?: never }
  | { figure?: ReactNode; actions?: never }
)

export function PageHeader({ title, subtitle, sticky = false, actions, figure }: PageHeaderProps) {
  return (
    <header className={sticky ? `${styles.pageHeader} ${styles.sticky}` : styles.pageHeader}>
      <div className={styles.heading}>
        <h1 className={styles.title}>{title}</h1>
        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
      {figure && <div className={styles.figure}>{figure}</div>}
    </header>
  )
}
