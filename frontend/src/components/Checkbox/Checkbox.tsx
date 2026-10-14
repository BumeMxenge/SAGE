// A checkbox with its label, as in "This reflects my current academic record".
import type { ReactNode } from 'react'
import { CheckboxButton, CheckboxField, type CheckboxFieldProps } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import styles from './Checkbox.module.css'

type CheckboxProps = Pick<CheckboxFieldProps, 'isSelected' | 'defaultSelected' | 'onChange' | 'name'> & {
  children: ReactNode
}

export function Checkbox({ children, ...props }: CheckboxProps) {
  return (
    <CheckboxField {...props} className={styles.field}>
      <CheckboxButton className={styles.button}>
        <span className={styles.box}>
          <Icon name="check" />
        </span>
        {children}
      </CheckboxButton>
    </CheckboxField>
  )
}
