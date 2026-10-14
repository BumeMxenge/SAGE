// A question with a few answers shown as chips, and one chosen. The label is the question. It is a
// radio group, so a screen reader hears the question and then each answer.
import type { ReactNode } from 'react'
import { Label, RadioGroup, Text } from 'react-aria-components'
import styles from './ChoiceChips.module.css'

type ChoiceChipsProps = {
  label: string
  labelHidden?: boolean
  description?: string
  value: string | null
  onChange: (value: string) => void
  isDisabled?: boolean
  children: ReactNode
}

export function ChoiceChips({ label, labelHidden, description, children, ...props }: ChoiceChipsProps) {
  return (
    <RadioGroup {...props} className={styles.group} orientation="horizontal">
      <Label className={labelHidden ? 'visually-hidden' : styles.label}>{label}</Label>
      {description && (
        <Text slot="description" className={styles.description}>
          {description}
        </Text>
      )}
      <div className={styles.chips}>{children}</div>
    </RadioGroup>
  )
}
