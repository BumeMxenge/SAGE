// A checkbox with its label. A hidden label isn't offered: a checkbox always shows what it asks.
import type { ReactNode } from 'react'
import { CheckboxButton, CheckboxField, type CheckboxFieldProps, FieldError, Text } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import styles from './Checkbox.module.css'

type CheckboxProps = Omit<CheckboxFieldProps, 'className' | 'style' | 'children'> & {
  children: ReactNode
  description?: string
  errorMessage?: string
}

export function Checkbox({ children, description, errorMessage, ...props }: CheckboxProps) {
  return (
    <CheckboxField {...props} className={styles.field}>
      <CheckboxButton className={styles.button}>
        <span className={styles.box}>
          <Icon name="check" />
        </span>
        {children}
      </CheckboxButton>
      {description && (
        <Text slot="description" className={styles.text}>
          {description}
        </Text>
      )}
      <FieldError className={styles.error}>{errorMessage}</FieldError>
    </CheckboxField>
  )
}
