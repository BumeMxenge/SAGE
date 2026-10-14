// A drop-down for choosing one option, such as the plan switcher. Options are SelectItems, optionally
// grouped in SelectSections.
import type { ReactNode } from 'react'
import { Button, FieldError, Label, ListBox, Select as AriaSelect, type SelectProps as AriaSelectProps, SelectValue, Text } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import { Popover } from '@/components/Popover/Popover.tsx'
import listStyles from '@/components/Popover/Popover.module.css'
import styles from './Select.module.css'

type SelectProps = Omit<AriaSelectProps<object>, 'className' | 'style' | 'children'> & {
  label: string
  labelHidden?: boolean
  description?: string
  errorMessage?: string
  children: ReactNode
}

export function Select({ label, labelHidden, description, errorMessage, children, ...props }: SelectProps) {
  return (
    <AriaSelect {...props} className={styles.select}>
      <Label className={labelHidden ? 'visually-hidden' : styles.label}>{label}</Label>
      <Button className={styles.trigger}>
        <SelectValue className={styles.value} />
        <Icon name="keyboard_arrow_down" />
      </Button>
      {description && (
        <Text slot="description" className={styles.description}>
          {description}
        </Text>
      )}
      <FieldError className={styles.error}>{errorMessage}</FieldError>
      <Popover>
        <ListBox className={listStyles.list}>{children}</ListBox>
      </Popover>
    </AriaSelect>
  )
}
