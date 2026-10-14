// The button for actions. Primary is the one main action, secondary is outlined, quiet is for
// supporting actions, and sign-in is the Microsoft sign-in button. While isPending, a spinner shows
// beside the label and screen readers hear "Loading".
import type { ReactNode } from 'react'
import { Button as AriaButton, type ButtonProps as AriaButtonProps, ProgressBar } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import styles from './Button.module.css'

type ButtonProps = Omit<AriaButtonProps, 'className' | 'style' | 'children'> & {
  variant?: 'primary' | 'secondary' | 'quiet' | 'sign-in'
  children: ReactNode
}

export function Button({ variant = 'primary', children, ...props }: ButtonProps) {
  return (
    <AriaButton {...props} className={`${styles.button} ${styles[variant === 'sign-in' ? 'signIn' : variant]}`}>
      {({ isPending }) => (
        <>
          {isPending && (
            <ProgressBar aria-label="Loading" isIndeterminate className={styles.spinner}>
              <Icon name="progress_activity" />
            </ProgressBar>
          )}
          {children}
        </>
      )}
    </AriaButton>
  )
}
