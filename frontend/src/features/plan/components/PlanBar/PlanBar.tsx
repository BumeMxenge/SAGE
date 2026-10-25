// The header and the term's row over a plan's term, or over two plans in compare. The header holds the
// plan's name and credits, or Compare's title, with its actions at the far end, and the row the term
// and the view, Calendar or Course List. While the sidebar and the assistant are both open, the view's
// options show only their icons, each named in a tooltip, as the prototype's do when the docked
// assistant takes their room. The row renders straight away, as it needs nothing from the API, and
// stays as it is while the plan or the pair arrives beneath it.
import type { ReactNode } from 'react'
import { Segment } from '@/components/inputs/SegmentedControl/Segment.tsx'
import { SegmentedControl } from '@/components/inputs/SegmentedControl/SegmentedControl.tsx'
import { Tooltip } from '@/components/overlays/Tooltip/Tooltip.tsx'
import { termLabels } from '@/lib/copy.ts'
import { type PlanTerm, planTerms } from '@/lib/planAddress.ts'
import type { View } from '../TermView/TermView.tsx'
import styles from './PlanBar.module.css'

type PlanBarProps = {
  term: PlanTerm
  onTermChange: (term: PlanTerm) => void
  view: View
  onViewChange: (view: View) => void
  iconOnly: boolean
  children: ReactNode // the header
}

export function PlanBar({ term, onTermChange, view, onViewChange, iconOnly, children }: PlanBarProps) {
  return (
    <div className={styles.bar}>
      <div className={styles.header}>{children}</div>
      <div className={styles.controls}>
        <SegmentedControl
          label="Term"
          selectedKey={term}
          onChange={(key) => {
            const chosen = planTerms.find((each) => each === key)
            if (chosen) onTermChange(chosen)
          }}
        >
          {planTerms.map((each) => (
            <Segment key={each} id={each}>
              {termLabels[each]}
            </Segment>
          ))}
        </SegmentedControl>
        <SegmentedControl label="View" selectedKey={view} onChange={(key) => onViewChange(key === 'list' ? 'list' : 'calendar')}>
          <Tooltip text="Calendar" isDisabled={!iconOnly}>
            <Segment id="calendar" icon={iconOnly ? 'calendar_today' : undefined}>
              Calendar
            </Segment>
          </Tooltip>
          <Tooltip text="Course List" isDisabled={!iconOnly}>
            <Segment id="list" icon={iconOnly ? 'format_list_bulleted' : undefined}>
              Course List
            </Segment>
          </Tooltip>
        </SegmentedControl>
      </div>
    </div>
  )
}
