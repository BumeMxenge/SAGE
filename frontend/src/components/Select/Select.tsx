// A drop-down for choosing one option, such as the plan switcher or a course's outcome. It has no
// visible label, as in the prototypes; the label is still there for screen readers. Options are
// SelectItems. The placeholder shows until something is chosen.
import type { ReactNode } from 'react'
import { Button, Label, ListBox, Select as AriaSelect, type SelectProps as AriaSelectProps, SelectValue } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import { Popover } from '@/components/Popover/Popover.tsx'
import listStyles from '@/components/Popover/Popover.module.css'
import styles from './Select.module.css'

type SelectProps = Pick<
  AriaSelectProps<object>,
  'selectedKey' | 'defaultSelectedKey' | 'onSelectionChange' | 'placeholder' | 'name'
> & {
  label: string
  children: ReactNode
}

export function Select({ label, children, ...props }: SelectProps) {
  return (
    <AriaSelect {...props}>
      <Label className="visually-hidden">{label}</Label>
      <Button className={styles.trigger}>
        <SelectValue className={styles.value} />
        <Icon name="keyboard_arrow_down" />
      </Button>
      <Popover>
        <ListBox className={listStyles.list}>{children}</ListBox>
      </Popover>
    </AriaSelect>
  )
}
