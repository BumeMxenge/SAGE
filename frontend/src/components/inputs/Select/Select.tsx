// A drop-down for choosing one option, such as the plan switcher or a course's outcome. It has no
// visible label, as in the prototypes; the label is still there for screen readers. Options are
// SelectItems. The placeholder shows until something is chosen, and then only the chosen option's
// name: its codes and credits stay in the list. A long name ends in an ellipsis within the plan
// switcher's width, and a screen reader still reads all of it. The list opens below, from the left
// edge, as the plan switcher does. It is outlined, as the plan switcher is, or plain, as the
// review's outcomes are in edit mode: the value and its arrow in the text around them. Quiet shows
// its label in place of the value, for a choice the page already names beside it, as Compare with
// Another Plan does under its panel's title.
import type { ReactNode } from 'react'
import { Button, Label, Select as AriaSelect, type SelectProps as AriaSelectProps, SelectValue } from 'react-aria-components'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import { Popover } from '@/components/overlays/Popover/Popover.tsx'
import outline from '@/styles/outline.module.css'
import { OptionList } from './OptionList.tsx'
import styles from './Select.module.css'

type Variant = 'outlined' | 'plain' | 'quiet'

type SelectProps = Pick<AriaSelectProps<object>, 'selectedKey' | 'onSelectionChange' | 'placeholder'> & {
  label: string
  variant?: Variant
  children: ReactNode
}

const variantClass: Record<Variant, string> = { outlined: outline.outline, plain: styles.plain, quiet: styles.quiet }

export function Select({ label, variant = 'outlined', children, ...props }: SelectProps) {
  const value = (
    <SelectValue className={variant === 'quiet' ? 'visually-hidden' : styles.value}>
      {({ isPlaceholder, selectedText, defaultChildren }) => (isPlaceholder ? defaultChildren : selectedText)}
    </SelectValue>
  )
  return (
    <AriaSelect {...props}>
      <Label className="visually-hidden">{label}</Label>
      <Button className={`${styles.trigger} ${variantClass[variant]}`}>
        {value}
        {/* The button is named by its value and label, so the label shown here isn't read twice */}
        {variant === 'quiet' && <span aria-hidden="true">{label}</span>}
        <Icon name="keyboard_arrow_down" />
      </Button>
      <Popover placement="bottom start">
        <OptionList>{children}</OptionList>
      </Popover>
    </AriaSelect>
  )
}
