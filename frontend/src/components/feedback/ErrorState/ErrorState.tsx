// What shows when something fails or blocks the way: an icon, a title, a message, and what gets past
// it below. The error sheet draws three kinds. A region error replaces one area that didn't load and
// keeps the rest usable, with an optional reference code so support can trace the failure. Its tone is
// danger when something failed (case 06), or warning when SAGE is waiting to try again (case 10). A
// screen reader announces it as soon as it appears. An inline error is a tinted row inside a form,
// such as a sign-in that didn't complete, above the button that tries again (cases 01 and 05). Its
// danger tone is announced too; its warning tone is plain text, for notes that arrive with the page.
// A blocking page is the whole page, so its title is the page's h1 and it has a larger title on a
// round grey tile (case 02).
import type { ReactNode } from 'react'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import type { IconName } from '@/components/brand/Icon/icons.ts'
import styles from './ErrorState.module.css'

type ErrorStateProps = {
  icon: Exclude<IconName, 'favorite'>
  title: string
  message: string
  reference?: string
  children?: ReactNode
} & ({ variant: 'region' | 'inline'; tone: 'danger' | 'warning' } | { variant: 'page'; tone?: never })

// A blocking page's title is its h1, and a region's a heading. An inline row sits inside a form, so
// its title is bold text, not another heading in the page's outline.
const titleElement = { page: 'h1', region: 'h2', inline: 'p' } as const

export function ErrorState({ variant, tone, icon, title, message, reference, children }: ErrorStateProps) {
  const Title = titleElement[variant]
  const announced = variant === 'region' || (variant === 'inline' && tone === 'danger')
  return (
    <div role={announced ? 'alert' : undefined} className={styles.errorState} data-variant={variant} data-tone={tone}>
      <span aria-hidden="true" className={styles.tile}>
        <Icon name={icon} />
      </span>
      <Title className={styles.title}>{title}</Title>
      <p className={styles.message}>{message}</p>
      <div className={styles.actions}>
        {children}
        {reference && <p className={styles.reference}>Reference {reference}</p>}
      </div>
    </div>
  )
}
