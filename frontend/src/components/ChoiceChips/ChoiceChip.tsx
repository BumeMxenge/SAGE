// One answer of ChoiceChips. The chosen chip shows a tick as well as a darker border.
import type { ReactNode } from 'react'
import { RadioButton, RadioField } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import styles from './ChoiceChips.module.css'

export function ChoiceChip({ value, isDisabled, children }: { value: string; isDisabled?: boolean; children: ReactNode }) {
  return (
    <RadioField value={value} isDisabled={isDisabled}>
      <RadioButton className={styles.chip}>
        {({ isSelected }) => (
          <>
            {isSelected && <Icon name="check" />}
            {children}
          </>
        )}
      </RadioButton>
    </RadioField>
  )
}
