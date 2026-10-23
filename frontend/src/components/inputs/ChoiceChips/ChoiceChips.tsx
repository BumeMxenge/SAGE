// A question with a few answers shown as chips. One may be chosen, and pressing the chosen one again
// clears it, as in the prototype's questionnaire. It is a radio group named by the question, so a
// screen reader hears the question and then each answer, and the arrow keys move between the chips.
// An answer that can't be chosen still takes focus, so the arrow keys and a screen reader still reach
// it: it is marked unavailable, pressing it changes nothing, and its reason is written under the chips
// for everyone to read, never on hover alone.
import { type ReactNode, useId } from 'react'
import { ToggleButtonGroup } from 'react-aria-components'
import { ChoiceChip } from './ChoiceChip.tsx'
import styles from './ChoiceChips.module.css'

export type Choice = {
  value: string
  label: ReactNode
  unavailable?: string // why it can't be chosen, as a sentence
}

type ChoiceChipsProps = {
  label: string
  description?: string
  choices: Choice[]
  value: string | null
  onChange: (value: string | null) => void
  // Focus the chosen chip, or else the first that can be chosen, as the chips appear
  takeFocus?: boolean
}

export function ChoiceChips({ label, description, choices, value, onChange, takeFocus = false }: ChoiceChipsProps) {
  const id = useId()
  const reasonId = (choice: Choice) => `${id}-${choice.value}`
  const unavailable = choices.filter((choice) => choice.unavailable)
  const focused = takeFocus
    ? (choices.find((choice) => choice.value === value) ?? choices.find((choice) => !choice.unavailable))
    : undefined
  return (
    <div className={styles.group}>
      <span id={`${id}-label`} className={styles.label}>
        {label}
      </span>
      {description && (
        <span id={`${id}-description`} className={styles.description}>
          {description}
        </span>
      )}
      <ToggleButtonGroup
        aria-labelledby={`${id}-label`}
        aria-describedby={description && `${id}-description`}
        selectionMode="single"
        selectedKeys={value === null ? [] : [value]}
        onSelectionChange={(keys) => {
          if (keys.size === 0) return onChange(null)
          const [key] = keys // single selection, so one key
          if (!unavailable.some((choice) => choice.value === key)) onChange(String(key))
        }}
        className={styles.chips}
      >
        {choices.map((choice) => (
          <ChoiceChip
            key={choice.value}
            id={choice.value}
            reasonId={choice.unavailable && reasonId(choice)}
            takeFocus={choice === focused}
          >
            {choice.label}
          </ChoiceChip>
        ))}
      </ToggleButtonGroup>
      {unavailable.length > 0 && (
        <div className={styles.reasons}>
          {unavailable.map((choice) => (
            <p key={choice.value} id={reasonId(choice)} className={styles.reason}>
              {choice.unavailable}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
