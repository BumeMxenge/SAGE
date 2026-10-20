// A row of options where exactly one is chosen, such as Sem 1, Sem 2, Winter and Summer. The label
// names the group for screen readers. It is as wide as its options, or with fill as wide as its place,
// shared equally between them, as the course picker's is.
import type { ReactNode } from 'react'
import { ToggleButtonGroup } from 'react-aria-components'
import styles from './SegmentedControl.module.css'

type SegmentedControlProps = {
  label: string
  selectedKey: string
  onChange: (key: string) => void
  fill?: boolean
  children: ReactNode
}

export function SegmentedControl({ label, selectedKey, onChange, fill = false, children }: SegmentedControlProps) {
  return (
    <ToggleButtonGroup
      aria-label={label}
      data-fill={fill || undefined}
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
