// The heart that marks a favourite. The label names it, such as "Favourite ECO1006F", and screen
// readers hear whether it is on. On shows a filled heart.
import { ToggleButton as AriaToggleButton, type ToggleButtonProps as AriaToggleButtonProps } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import { Tooltip } from '@/components/Tooltip/Tooltip.tsx'
import styles from './ToggleButton.module.css'

type ToggleButtonProps = Omit<AriaToggleButtonProps, 'className' | 'style' | 'children' | 'aria-label' | 'isDisabled'> & {
  label: string
}

export function ToggleButton({ label, ...props }: ToggleButtonProps) {
  return (
    <Tooltip text={label}>
      <AriaToggleButton {...props} aria-label={label} className={styles.toggleButton}>
        {({ isSelected }) => <Icon name="favorite" filled={isSelected} />}
      </AriaToggleButton>
    </Tooltip>
  )
}
