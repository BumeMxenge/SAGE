// The button for actions. Primary is the one main action, secondary is outlined, quiet is for
// supporting actions such as Back, and sign-in is the Microsoft sign-in button, as long as the
// sign-in form. An icon can sit before the label, or stand alone: then the label names the button for
// screen readers, as Compare does when the sidebar and the assistant are both open.
import type { ReactNode } from 'react'
import { Button as AriaButton, type ButtonProps as AriaButtonProps } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import type { IconName } from '@/components/Icon/icons.ts'
import outline from '@/styles/outline.module.css'
import styles from './Button.module.css'

type Variant = 'primary' | 'secondary' | 'quiet' | 'sign-in'
type ButtonIcon = Exclude<IconName, 'favorite'>

type ButtonProps = Omit<AriaButtonProps, 'className' | 'style' | 'children' | 'isPending'> & { variant?: Variant } & (
    | { icon?: ButtonIcon; iconOnly?: false; children: ReactNode }
    | { icon: ButtonIcon; iconOnly: true; children: string }
  )

const variantClass: Record<Variant, string> = {
  primary: styles.primary,
  secondary: `${styles.secondary} ${outline.outline}`,
  quiet: styles.quiet,
  'sign-in': styles.signIn,
}

export function Button({ variant = 'primary', icon, iconOnly, children, ...props }: ButtonProps) {
  return (
    <AriaButton
      {...props}
      aria-label={iconOnly ? children : undefined}
      className={`${styles.button} ${variantClass[variant]} ${iconOnly ? styles.iconOnly : ''}`}
    >
      {icon && <Icon name={icon} />}
      {!iconOnly && children}
    </AriaButton>
  )
}
