// A switch for a setting that is on or off, with its label beside it.
import type { ReactNode } from 'react'
import { SwitchButton, SwitchField, type SwitchFieldProps } from 'react-aria-components'
import styles from './Switch.module.css'

type SwitchProps = Omit<SwitchFieldProps, 'className' | 'style' | 'children'> & { children: ReactNode }

export function Switch({ children, ...props }: SwitchProps) {
  return (
    <SwitchField {...props} className={styles.field}>
      <SwitchButton className={styles.button}>
        <span className={styles.track}>
          <span className={styles.handle} />
        </span>
        {children}
      </SwitchButton>
    </SwitchField>
  )
}
