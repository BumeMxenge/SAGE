import { useState } from 'react'
import { DropZone } from '@/components/DropZone/DropZone.tsx'
import { SearchField } from '@/components/SearchField/SearchField.tsx'
import { TextArea } from '@/components/TextArea/TextArea.tsx'
import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import styles from './DesignSystem.module.css'

export function FieldsSection() {
  const [chosen, setChosen] = useState<string[]>([])
  return (
    <Section
      title="Search, Chat and Upload"
      intro="The only places a student types are the search fields and the chat box, and the only upload is the transcript. None shows a label, so each has one for screen readers only. Drag a PDF over the drop zone to see its dragging state, or use the Choose button."
    >
      <div className={styles.samples}>
        <Sample label="Search: empty, filled with its clear button, and waiting while SAGE is busy">
          <div className={styles.wide}>
            <SearchField label="Search electives" placeholder="Search electives by code, topic or lecturer" />
          </div>
          <div className={styles.wide}>
            <SearchField label="Search electives" placeholder="Search electives by code, topic or lecturer" defaultValue="ABC" />
          </div>
          <div className={styles.wide}>
            <SearchField label="Search electives" placeholder="Search electives by code, topic or lecturer" isDisabled />
          </div>
        </Sample>
        <Sample label="Chat box">
          <div className={styles.narrow}>
            <TextArea label="Ask about this plan" placeholder="Ask about this plan" />
          </div>
        </Sample>
        <Sample label={`Transcript upload, light only: rest and error. Last chosen: ${chosen.length ? chosen.join(', ') : 'nothing'}`}>
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
