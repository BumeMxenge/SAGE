// The button for actions. Primary is the one main action, secondary is outlined, quiet is for
// supporting actions such as Back, danger confirms a destructive action such as Remove Course, and
// sign-in is onboarding's long dark button, as long as the sign-in form: Continue with UCT Email, and
// Account Created's Next. Dark has sign-in's colours at a secondary button's size, as Done Editing
// does. An icon can sit before the label, or stand alone: then the label names the button for screen
// readers, as Compare does when the sidebar and the assistant are both open.
import type { ReactNode } from 'react'
import { Button as AriaButton, type ButtonProps as AriaButtonProps } from 'react-aria-components'
import { Icon, type PlainIconName } from '@/components/brand/Icon/Icon.tsx'
import outline from '@/styles/outline.module.css'
import styles from './Button.module.css'

type Variant = 'primary' | 'secondary' | 'quiet' | 'sign-in' | 'dark' | 'danger'

type ButtonProps = Omit<AriaButtonProps, 'className' | 'style' | 'children' | 'isPending'> & { variant?: Variant } & (
    | { icon?: PlainIconName; iconOnly?: false; children: ReactNode }
    | { icon: PlainIconName; iconOnly: true; children: string }
  )

const variantClass: Record<Variant, string> = {
  primary: styles.primary,
  secondary: `${styles.secondary} ${outline.outline}`,
  quiet: styles.quiet,
  'sign-in': styles.signIn,
  dark: styles.dark,
  danger: `${styles.primary} ${styles.danger}`,
}

export function Button({ variant = 'primary', icon, iconOnly, children, ...props }: ButtonProps) {
  return (
    <AriaButton
      // A label the caller gives wins over the one an icon-only button takes from its children
      aria-label={iconOnly ? children : undefined}
      {...props}
      className={`${styles.button} ${variantClass[variant]} ${iconOnly ? styles.iconOnly : ''}`}
    >
      {icon && <Icon name={icon} />}
      {!iconOnly && children}
    </AriaButton>
  )
}
