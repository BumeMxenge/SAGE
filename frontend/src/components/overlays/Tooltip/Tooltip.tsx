// A short label that appears when the control inside it is hovered or focused. The control must be a
// React Aria one, such as Button or Link. Hover waits 300 ms so sweeping across a row of buttons doesn't
// flash every label. Keyboard focus shows it at once. It sits above its control unless placed
// elsewhere, as the sidebar's rail puts each icon's to its right, and is switched off while the
// control's own label is on screen, as the open sidebar's are.
import type { ReactElement } from 'react'
import { Tooltip as AriaTooltip, type TooltipProps as AriaTooltipProps, TooltipTrigger } from 'react-aria-components'
import styles from './Tooltip.module.css'

type TooltipProps = {
  text: string
  placement?: AriaTooltipProps['placement']
  isDisabled?: boolean
  children: ReactElement
}

export function Tooltip({ text, placement, isDisabled, children }: TooltipProps) {
  return (
    <TooltipTrigger delay={300} isDisabled={isDisabled}>
      {children}
      <AriaTooltip className={styles.tooltip} offset={8} placement={placement}>
        {text}
      </AriaTooltip>
    </TooltipTrigger>
  )
}
