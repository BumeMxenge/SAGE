import { useState } from 'react'
import { Checkbox } from '@/components/Checkbox/Checkbox.tsx'
import { ChoiceChip } from '@/components/ChoiceChips/ChoiceChip.tsx'
import { ChoiceChips } from '@/components/ChoiceChips/ChoiceChips.tsx'
import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import styles from './DesignSystem.module.css'

export function ChoicesSection() {
  const [answer, setAnswer] = useState<string | null>('none')
  return (
    <Section
      title="Choices"
      intro="The questionnaire's chips and the review step's checkbox. A chosen chip has a tick as well as a darker border. A chip that clashes with an answer already chosen fades and can't be picked. The checkbox border reaches 3:1."
    >
      <div className={styles.samples}>
        <Sample label="Choice chips: one chosen, one that clashes">
          <ChoiceChips
            label="Which timetable shape do you prefer?"
            description="Single choice."
            value={answer}
            onChange={setAnswer}
          >
            <ChoiceChip value="none">No timetable-shape preference</ChoiceChip>
            <ChoiceChip value="mornings">Minimise 8am starts</ChoiceChip>
            <ChoiceChip value="lunch" isDisabled>
              Keep the 13:00 lunch hour free
            </ChoiceChip>
          </ChoiceChips>
        </Sample>
        <Sample label="Checkbox: off and on">
          <Checkbox>This reflects my current academic record</Checkbox>
          <Checkbox defaultSelected>This reflects my current academic record</Checkbox>
        </Sample>
      </div>
    </Section>
  )
}
