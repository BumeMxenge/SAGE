// The assistant, docked beside the plan at a plan's own address: the named aside approved difference
// 6 asks for. Folded, it's a strip holding Open Assistant, the icon button approved difference 9 puts
// in place of the prototype's rotated label. Open, its header names the plan or pair the address puts
// on screen. A plan that doesn't exist has no assistant. Pressing a toggle moves focus to the one that
// replaces it, as the sidebar's do, and what is folded away isn't there to take focus.
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { IconButton } from '@/components/actions/IconButton/IconButton.tsx'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import { ApiError } from '@/lib/api.ts'
import { usePlanAddress } from '@/lib/planAddress.ts'
import { queries } from '@/lib/queryKeys.ts'
import styles from './AssistantRail.module.css'

type AssistantRailProps = { open: boolean; onOpenChange: (open: boolean) => void }

export function AssistantRail({ open, onOpenChange }: AssistantRailProps) {
  const { planId, compareWith } = usePlanAddress()
  // Only after a toggle press, never as a page opens
  const [moveFocus, setMoveFocus] = useState(false)
  // The plan or pair on screen, from the reads the plan view makes
  const single = useQuery({ ...queries.plan(planId), enabled: compareWith === null })
  const pair = useQuery({ ...queries.comparison(planId, compareWith ?? planId), enabled: compareWith !== null })

  const error = compareWith === null ? single.error : pair.error
  if (error instanceof ApiError && error.code === 'plan_not_found') return null

  function toggle() {
    onOpenChange(!open)
    setMoveFocus(true)
  }

  const reading =
    compareWith === null
      ? single.data && `Reading ${single.data.name}`
      : pair.data && `Comparing ${pair.data.first.name} and ${pair.data.second.name}`

  return (
    <aside aria-label="Assistant" data-folded={!open || undefined} className={styles.rail}>
      {open ? (
        <header className={styles.header}>
          <Icon name="chat_bubble" />
          <div className={styles.heading}>
            <h2 className={styles.title}>Assistant</h2>
            {reading && <p className={styles.reading}>{reading}</p>}
          </div>
          <IconButton
            label="Collapse Assistant"
            icon="chevron_right"
            // Only after a toggle press, never as a page opens: see moveFocus
            // oxlint-disable-next-line jsx-a11y/no-autofocus
            autoFocus={moveFocus}
            onPress={toggle}
          />
        </header>
      ) : (
        <IconButton
          label="Open Assistant"
          icon="chat_bubble"
          // Only after a toggle press, never as a page opens: see moveFocus
          // oxlint-disable-next-line jsx-a11y/no-autofocus
          autoFocus={moveFocus}
          onPress={toggle}
        />
      )}
    </aside>
  )
}
