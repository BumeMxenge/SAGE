// The SAGE logo at a fixed size. Both theme files are in the page and CSS shows the one that matches
// the theme, so Match System needs no JavaScript and nothing flashes. The compact logo is small in the
// sidebar, as the planner draws it, and larger in onboarding's header. The Microsoft variant is
// Microsoft's own mark for the sign-in button, kept unaltered.
import { useId } from 'react'
import CompactDark from '@brand/sage-logo-compact-dark.svg?react'
import CompactLight from '@brand/sage-logo-compact-light.svg?react'
import FullDark from '@brand/sage-logo-full-dark.svg?react'
import FullLight from '@brand/sage-logo-full-light.svg?react'
import MarkDark from '@brand/sage-logo-mark-dark.svg?react'
import MarkLight from '@brand/sage-logo-mark-light.svg?react'
import Microsoft from './microsoft.svg?react'
import styles from './Logo.module.css'

const themed = {
  full: { light: FullLight, dark: FullDark },
  compact: { light: CompactLight, dark: CompactDark },
  mark: { light: MarkLight, dark: MarkDark },
}

type LogoProps = { variant: 'compact'; small?: boolean } | { variant: 'full' | 'mark' | 'microsoft'; small?: never }

export function Logo({ variant, small = false }: LogoProps) {
  // Each file names itself with <title id>, so two logos on a page need different ids
  const id = useId()
  if (variant === 'microsoft') {
    return <Microsoft className={`${styles.logo} ${styles.microsoft}`} aria-hidden="true" focusable="false" />
  }
  const { light: Light, dark: Dark } = themed[variant]
  const size = `${styles[variant]} ${small ? styles.small : ''}`
  return (
    <>
      <Light className={`${styles.logo} ${size} ${styles.light}`} titleId={`${id}-light`} />
      <Dark className={`${styles.logo} ${size} ${styles.dark}`} titleId={`${id}-dark`} />
    </>
  )
}
