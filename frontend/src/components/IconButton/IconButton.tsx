// A button that shows only an icon. The label names it for screen readers and appears as a tooltip.
import { Button as AriaButton, type ButtonProps as AriaButtonProps } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import type { IconName } from '@/components/Icon/icons.ts'
import { Tooltip } from '@/components/Tooltip/Tooltip.tsx'
import styles from './IconButton.module.css'

type IconButtonProps = Omit<AriaButtonProps, 'className' | 'style' | 'children' | 'aria-label'> & {
  label: string
  icon: Exclude<IconName, 'favorite'>
}

export function IconButton({ label, icon, ...props }: IconButtonProps) {
  return (
    <Tooltip text={label}>
      <AriaButton {...props} aria-label={label} className={styles.iconButton}>
        <Icon name={icon} />
      </AriaButton>
    </Tooltip>
  )
}
