// What shows when something fails or blocks the way: an icon, a title, a message, and what gets past
// it below. The error sheet draws three kinds. A region error replaces one area that didn't load and
// keeps the rest usable, with an optional reference code so support can trace the failure. Its tone is
// danger when something failed (case 06), or warning when SAGE is waiting to try again (case 10). A
// screen reader announces it as soon as it appears. An inline error is a row tinted in the warning
// tone inside a form or a card, for a note that arrives with the page, so it is plain text.
// A message error is a reply that failed in a conversation, where the reply would be: the inline row
// with no tint, in the danger text colour (case 09). It is announced too. A blocking page is the
// whole page, so its title is the page's h1 and it has a larger title on a round grey tile (case 02).
import type { ReactNode } from 'react'
import { Icon, type PlainIconName } from '@/components/brand/Icon/Icon.tsx'
import styles from './ErrorState.module.css'

type ErrorStateProps = {
  icon: PlainIconName
  title: string
  message: string
  reference?: string
  children?: ReactNode
} & (
  | { variant: 'region'; tone: 'danger' | 'warning' }
  | { variant: 'inline'; tone: 'warning' }
  | { variant: 'page' | 'message'; tone?: never }
)

// A blocking page's title is its h1, and a region's a heading. An inline row sits inside a form, and a
// message error inside a conversation, so their titles are bold text, not more headings in the page's
// outline.
const titleElement = { page: 'h1', region: 'h2', inline: 'p', message: 'p' } as const

export function ErrorState({ variant, tone, icon, title, message, reference, children }: ErrorStateProps) {
  const Title = titleElement[variant]
  const announced = variant === 'region' || variant === 'message'
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
