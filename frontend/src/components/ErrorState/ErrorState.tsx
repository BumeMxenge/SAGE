// What shows when something fails or blocks the way: an icon on a tile, a title, a message, and what
// gets past it below. The error sheet draws two kinds. A region error replaces one area that didn't
// load and keeps the rest usable (case 06): a danger tile, and an optional reference code so support
// can trace the failure. A screen reader announces it as soon as it appears. A blocking page is the
// whole page, so its title is the page's h1 and it has a larger title on a round grey tile (case 02).
import type { ReactNode } from 'react'
import { Icon } from '@/components/Icon/Icon.tsx'
import type { IconName } from '@/components/Icon/icons.ts'
import styles from './ErrorState.module.css'

type ErrorStateProps = {
  variant: 'region' | 'page'
  icon: Exclude<IconName, 'favorite'>
  title: string
  message: string
  reference?: string
  children?: ReactNode
}

export function ErrorState({ variant, icon, title, message, reference, children }: ErrorStateProps) {
  const Heading = variant === 'page' ? 'h1' : 'h2'
  return (
    <div role={variant === 'region' ? 'alert' : undefined} className={styles.errorState} data-variant={variant}>
      <span aria-hidden="true" className={styles.tile}>
        <Icon name={icon} />
      </span>
      <Heading className={styles.title}>{title}</Heading>
      <p className={styles.message}>{message}</p>
      <div className={styles.actions}>
        {children}
        {reference && <p className={styles.reference}>Reference {reference}</p>}
      </div>
    </div>
  )
}
