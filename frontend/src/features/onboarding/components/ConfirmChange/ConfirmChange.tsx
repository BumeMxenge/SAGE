// The question before one change to the review: what the change is, as a list of facts, then a button
// to step back and one to go ahead. Adding a course, changing an outcome and removing a course each
// ask this way. Escape, the close button and a click outside all step back.
import type { ReactNode } from 'react'
import { Button } from '@/components/actions/Button/Button.tsx'
import { Dialog } from '@/components/overlays/Dialog/Dialog.tsx'
import styles from './ConfirmChange.module.css'

type ConfirmChangeProps = {
  title: string
  lead: string
  // A fact can be in danger text, as the course being removed is
  facts: { term: string; value: ReactNode; danger?: boolean }[]
  cancelLabel: string
  confirmLabel: string
  // A destructive change confirms with the danger button
  destructive?: boolean
  isConfirmDisabled?: boolean
  onCancel: () => void
  onConfirm: () => void
}

export function ConfirmChange({
  title,
  lead,
  facts,
  cancelLabel,
  confirmLabel,
  destructive = false,
  isConfirmDisabled = false,
  onCancel,
  onConfirm,
}: ConfirmChangeProps) {
  return (
    <Dialog title={title} onClose={onCancel}>
      <p className={styles.lead}>{lead}</p>
      <dl className={styles.facts}>
        {facts.map(({ term, value, danger }) => (
          <div key={term} className={styles.fact}>
            <dt>{term}</dt>
            <dd data-tone={danger ? 'danger' : undefined}>{value}</dd>
          </div>
        ))}
      </dl>
      <div className={styles.buttons}>
        <Button variant="quiet" onPress={onCancel}>
          {cancelLabel}
        </Button>
        <Button variant={destructive ? 'danger' : 'primary'} isDisabled={isConfirmDisabled} onPress={onConfirm}>
          {confirmLabel}
        </Button>
      </div>
    </Dialog>
  )
}
