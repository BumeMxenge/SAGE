// The top of a page in the app, holding its h1: a title, an optional subtitle and optional actions,
// always left-aligned at the reading width. A blocking error page has none: its ErrorState holds the h1.
import type { ReactNode } from 'react'
import styles from './PageHeader.module.css'

type PageHeaderProps = { title: string; subtitle?: string; actions?: ReactNode }

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <header className={styles.pageHeader}>
      <div>
        <h1 className={styles.title}>{title}</h1>
        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </header>
  )
}
