// The button for actions. Primary is the one main action, secondary is outlined, quiet is for
// supporting actions such as Back, and sign-in is the Microsoft sign-in button, as long as the
// sign-in form.
import type { ReactNode } from 'react'
import { Button as AriaButton, type ButtonProps as AriaButtonProps } from 'react-aria-components'
import styles from './Button.module.css'

type ButtonProps = Omit<AriaButtonProps, 'className' | 'style' | 'children' | 'isPending'> & {
  variant?: 'primary' | 'secondary' | 'quiet' | 'sign-in'
  children: ReactNode
}

export function Button({ variant = 'primary', children, ...props }: ButtonProps) {
  return (
    <AriaButton {...props} className={`${styles.button} ${styles[variant === 'sign-in' ? 'signIn' : variant]}`}>
      {children}
    </AriaButton>
  )
}
