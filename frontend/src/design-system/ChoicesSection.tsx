import { useState } from 'react'
import { Checkbox } from '@/components/Checkbox/Checkbox.tsx'
import { ChoiceChip } from '@/components/ChoiceChips/ChoiceChip.tsx'
import { ChoiceChips } from '@/components/ChoiceChips/ChoiceChips.tsx'
import { Switch } from '@/components/Switch/Switch.tsx'
import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import styles from './DesignSystem.module.css'

export function ChoicesSection() {
  const [answer, setAnswer] = useState<string | null>('none')
  return (
    <Section
      title="Choices"
      intro="Chips, checkboxes and switches. A chosen chip has a tick as well as a darker border, and the checkbox and switch borders reach 3:1."
    >
      <div className={styles.samples}>
        <Sample label="Choice chips: a question, one chosen, one disabled">
          <ChoiceChips label="Which timetable shape do you prefer?" value={answer} onChange={setAnswer}>
            <ChoiceChip value="none">No timetable-shape preference</ChoiceChip>
            <ChoiceChip value="mornings">Minimise 8am starts</ChoiceChip>
            <ChoiceChip value="lunch" isDisabled>
              Keep the 13:00 lunch hour free
            </ChoiceChip>
          </ChoiceChips>
        </Sample>
        <Sample label="Checkbox: off, on, disabled, error">
          <Checkbox>This reflects my current academic record</Checkbox>
          <Checkbox defaultSelected>This reflects my current academic record</Checkbox>
          <Checkbox isDisabled>This reflects my current academic record</Checkbox>
          <Checkbox isInvalid errorMessage="Tick this box to go on">
            This reflects my current academic record
          </Checkbox>
        </Sample>
        <Sample label="Switch: off, on, disabled">
          <Switch>Notify me</Switch>
          <Switch defaultSelected>Notify me</Switch>
          <Switch isDisabled>Notify me</Switch>
        </Sample>
      </div>
    </Section>
  )
}
