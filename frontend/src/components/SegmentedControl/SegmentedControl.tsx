// A row of options where exactly one is chosen, such as Sem 1, Sem 2, Winter and Summer. The label
// names the group for screen readers.
import type { ReactNode } from 'react'
import { ToggleButtonGroup } from 'react-aria-components'
import styles from './SegmentedControl.module.css'

type SegmentedControlProps = {
  label: string
  selectedKey: string
  onChange: (key: string) => void
  children: ReactNode
}

export function SegmentedControl({ label, selectedKey, onChange, children }: SegmentedControlProps) {
  return (
    <ToggleButtonGroup
      aria-label={label}
      className={styles.segmentedControl}
      selectionMode="single"
      disallowEmptySelection
      selectedKeys={[selectedKey]}
      onSelectionChange={(keys) => {
        const [key] = keys // single selection, so never 'all'
        onChange(String(key))
      }}
    >
      {children}
    </ToggleButtonGroup>
  )
}
