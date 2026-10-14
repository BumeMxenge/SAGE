// A short label that appears when the control inside it is hovered or focused. The control must be a
// React Aria one, such as Button. Hover waits 300 ms so sweeping across a row of buttons doesn't flash
// every label. Keyboard focus shows it at once.
import type { ReactElement } from 'react'
import { Tooltip as AriaTooltip, TooltipTrigger } from 'react-aria-components'
import styles from './Tooltip.module.css'

type TooltipProps = { text: string; children: ReactElement }

export function Tooltip({ text, children }: TooltipProps) {
  return (
    <TooltipTrigger delay={300}>
      {children}
      <AriaTooltip className={styles.tooltip} offset={8}>
        {text}
      </AriaTooltip>
    </TooltipTrigger>
  )
}
