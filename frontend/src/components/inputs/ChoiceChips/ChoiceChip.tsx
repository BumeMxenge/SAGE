// One answer of ChoiceChips. The chosen chip shows a tick as well as a darker border. One that can't be
// chosen fades and shows the block icon, so the fade isn't all that marks it, and names its reason,
// under the chips, as its description. It is aria-disabled rather than disabled, so it keeps focus.
import type { ReactNode } from 'react'
import { ToggleButton } from 'react-aria-components'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import styles from './ChoiceChips.module.css'

type ChoiceChipProps = { id: string; reasonId: string | undefined; children: ReactNode }

export function ChoiceChip({ id, reasonId, children }: ChoiceChipProps) {
  const unavailable = reasonId !== undefined
  return (
    <ToggleButton
      id={id}
      aria-disabled={unavailable || undefined}
      aria-describedby={reasonId}
      data-unavailable={unavailable || undefined}
      className={styles.chip}
    >
      {({ isSelected }) => (
        <>
          {isSelected && <Icon name="check" />}
          {unavailable && <Icon name="block" />}
          {children}
        </>
      )}
    </ToggleButton>
  )
}
