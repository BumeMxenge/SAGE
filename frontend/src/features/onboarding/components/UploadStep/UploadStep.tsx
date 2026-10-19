// The transcript upload. The API reads the student's PDF in one request, with the PDF as the request's
// whole body, and keeps nothing. Nor does this page: once the PDF is read the File is let go, and only
// its name and size stay, for the card.
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { Button } from '@/components/actions/Button/Button.tsx'
import { IconButton } from '@/components/actions/IconButton/IconButton.tsx'
import { Card } from '@/components/content/Card/Card.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { DropZone } from '@/features/onboarding/components/DropZone/DropZone.tsx'
import { client, dataOf } from '@/lib/api.ts'
import type { components } from '@/lib/api-types.ts'
import styles from './UploadStep.module.css'

type Transcript = components['schemas']['Transcript']

// Nothing chosen yet, a PDF being read, or what the read found
type Upload =
  | { stage: 'choosing' }
  | { stage: 'reading'; file: File }
  | { stage: 'read'; name: string; size: number; transcript: Transcript }

const privacy = "SAGE deletes the PDF as soon as it's read and never stores it."

const hints = {
  choosing: 'Attach a PDF transcript to continue.',
  reading: 'Hold on while we read your transcript.',
  read: null,
}

const courses = (count: number) => `${count} ${count === 1 ? 'course' : 'courses'}`

// As the prototype writes a file's size: kilobytes below a megabyte, then megabytes to one place
function sizeOf(bytes: number): string {
  const megabyte = 1024 * 1024
  return bytes < megabyte ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / megabyte).toFixed(1)} MB`
}

export function UploadStep({ onContinue }: { onContinue: (transcript: Transcript) => void }) {
  const [upload, setUpload] = useState<Upload>({ stage: 'choosing' })
  const reading = useMutation({
    // The PDF itself is the body, as lib/api.ts explains
    mutationFn: (file: File) =>
      dataOf(
        client.POST('/v1/onboarding/transcript', {
          body: file as unknown as string,
          bodySerializer: (body) => body,
          headers: { 'Content-Type': 'application/pdf' },
        }),
      ),
    // The transcript moves into this step's state, so the cache keeps no copy of it or of the file
    gcTime: 0,
  })

  function choose([file]: File[]) {
    setUpload({ stage: 'reading', file })
    reading.mutate(file, {
      onSuccess: (transcript) => {
        setUpload({ stage: 'read', name: file.name, size: file.size, transcript })
        reading.reset()
      },
    })
  }

  function remove() {
    reading.reset()
    setUpload({ stage: 'choosing' })
  }

  const hint = hints[upload.stage]
  return (
    <div className={styles.upload}>
      <PageHeader
        title="Upload Your Transcript"
        subtitle={
          upload.stage === 'read'
            ? `All done. We found ${courses(upload.transcript.lines.length)} in your transcript. Continue to check them over. ${privacy}`
            : `We'll read your course history straight from your transcript. ${privacy}`
        }
      />
      {upload.stage === 'choosing' ? (
        <DropZone
          title="Upload your transcript"
          hint="Drag and drop a file here, or"
          buttonLabel="Choose PDF"
          note="PDF only · maximum 10 MB"
          acceptedFileTypes={['application/pdf']}
          onSelect={choose}
        />
      ) : (
        <Card
          level={2}
          title={upload.stage === 'read' ? upload.name : upload.file.name}
          meta={
            upload.stage === 'read' ? (
              <p className={styles.found}>
                PDF · {sizeOf(upload.size)} · {courses(upload.transcript.lines.length)} found
              </p>
            ) : (
              <p className={styles.status}>Reading your transcript…</p>
            )
          }
          actions={<IconButton label="Remove File" icon="close" onPress={remove} />}
        />
      )}
      <div className={styles.continue}>
        <Button isDisabled={upload.stage !== 'read'} onPress={() => upload.stage === 'read' && onContinue(upload.transcript)}>
          Continue
        </Button>
        {hint && <p className={styles.hint}>{hint}</p>}
      </div>
    </div>
  )
}
