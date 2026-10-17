// The floating panel behind Select and Menu. It must sit inside a React Aria trigger such as
// MenuTrigger. Its width follows the button it opens from, and it fades in and out.
import { Popover as AriaPopover, type PopoverProps as AriaPopoverProps } from 'react-aria-components'
import styles from './Popover.module.css'

export function Popover(props: Omit<AriaPopoverProps, 'className' | 'style'>) {
  return <AriaPopover {...props} className={styles.popover} />
}
