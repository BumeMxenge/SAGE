// A button that shows only an icon. The label names it for screen readers and appears as a tooltip.
// Given isSelected and onChange it is a toggle: the favourite heart, filled while it is on. Only the
// heart has a filled version, so it is the one icon that toggles.
import {
  Button as AriaButton,
  type ButtonProps as AriaButtonProps,
  ToggleButton as AriaToggleButton,
} from 'react-aria-components'
import { Icon, type PlainIconName } from '@/components/brand/Icon/Icon.tsx'
import { Tooltip } from '@/components/overlays/Tooltip/Tooltip.tsx'
import styles from './IconButton.module.css'

type ActionProps = Omit<AriaButtonProps, 'className' | 'style' | 'children' | 'aria-label' | 'isDisabled'> & {
  label: string
  icon: PlainIconName
}

type ToggleProps = { label: string; icon: 'favorite'; isSelected: boolean; onChange: (isSelected: boolean) => void }

export function IconButton(props: ActionProps | ToggleProps) {
  if (props.icon === 'favorite') {
    const { label, isSelected, onChange } = props
    return (
      <Tooltip text={label}>
        <AriaToggleButton
          isSelected={isSelected}
          onChange={onChange}
          aria-label={label}
          className={`${styles.iconButton} ${styles.toggle}`}
        >
          <Icon name="favorite" filled={isSelected} />
        </AriaToggleButton>
      </Tooltip>
    )
  }
  const { label, icon, ...buttonProps } = props
  return (
    <Tooltip text={label}>
      <AriaButton {...buttonProps} aria-label={label} className={styles.iconButton}>
        <Icon name={icon} />
      </AriaButton>
    </Tooltip>
  )
}
