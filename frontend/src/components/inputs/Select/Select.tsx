// A drop-down for choosing one option, such as the plan switcher or a course's outcome. It has no
// visible label, as in the prototypes; the label is still there for screen readers. Options are
// SelectItems. The placeholder shows until something is chosen, and then only the chosen option's
// name: its codes and credits stay in the list. The list opens below, from the left edge, as the plan
// switcher does.
import type { ReactNode } from 'react'
import { Button, Label, ListBox, Select as AriaSelect, type SelectProps as AriaSelectProps, SelectValue } from 'react-aria-components'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import { Popover } from '@/components/overlays/Popover/Popover.tsx'
import listStyles from '@/components/overlays/Popover/Popover.module.css'
import outline from '@/styles/outline.module.css'
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
      <Button className={`${styles.trigger} ${outline.outline}`}>
        <SelectValue className={styles.value}>
          {({ isPlaceholder, selectedText, defaultChildren }) => (isPlaceholder ? defaultChildren : selectedText)}
        </SelectValue>
        <Icon name="keyboard_arrow_down" />
      </Button>
      <Popover placement="bottom start">
        <ListBox className={`${listStyles.list} ${styles.list}`}>{children}</ListBox>
      </Popover>
    </AriaSelect>
  )
}
