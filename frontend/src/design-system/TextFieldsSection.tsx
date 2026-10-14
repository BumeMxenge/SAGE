import { useState } from 'react'
import { DropZone } from '@/components/DropZone/DropZone.tsx'
import { SearchField } from '@/components/SearchField/SearchField.tsx'
import { TextArea } from '@/components/TextArea/TextArea.tsx'
import { TextField } from '@/components/TextField/TextField.tsx'
import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import styles from './DesignSystem.module.css'

export function TextFieldsSection() {
  const [chosen, setChosen] = useState<string[]>([])
  return (
    <Section
      title="Text Fields"
      intro="Every field has a label. Where the design shows none, the label is hidden from view and still read out. Drag a PDF over the drop zone to see its dragging state, or use the Choose button."
    >
      <div className={styles.samples}>
        <Sample label="Text field: rest, with help text, disabled, error">
          <TextField label="Course code" placeholder="For example ABC1001F" />
          <TextField label="Course code" description="Letters and digits, as printed in the handbook" />
          <TextField label="Course code" isDisabled defaultValue="ABC1001F" />
          <TextField label="Course code" isInvalid errorMessage="That course is not in the handbook" defaultValue="ZZZ0000X" />
        </Sample>
        <Sample label="Text area: rest, error">
          <TextArea label="Ask about this plan" labelHidden placeholder="Ask about this plan" />
          <TextArea label="Ask about this plan" isInvalid errorMessage="Write a question first" />
        </Sample>
        <Sample label="Search field: empty, filled with its clear button, disabled">
          <SearchField label="Search electives" labelHidden placeholder="Search electives by code, topic or lecturer" />
          <SearchField label="Search electives" labelHidden defaultValue="ABC" />
          <SearchField label="Search electives" labelHidden isDisabled placeholder="Search electives" />
        </Sample>
        <Sample label={`Drop zone: rest and error. Last chosen: ${chosen.length ? chosen.join(', ') : 'nothing'}`}>
          <div className={styles.wide}>
            <DropZone
              title="Drop your transcript here"
              hint="PDF only. SAGE reads it, then deletes it."
              buttonLabel="Choose PDF"
              acceptedFileTypes={['application/pdf']}
              onSelect={(files) => setChosen(files.map((file) => file.name))}
            />
          </div>
          <div className={styles.wide}>
            <DropZone
              title="Drop your transcript here"
              buttonLabel="Choose PDF"
              acceptedFileTypes={['application/pdf']}
              onSelect={() => undefined}
              errorMessage="That file is not a PDF."
            />
          </div>
        </Sample>
      </div>
    </Section>
  )
}
