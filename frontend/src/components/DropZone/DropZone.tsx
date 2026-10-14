// Where a file is dropped or chosen. There are three ways in, so nobody is shut out: drop it on the
// zone, press the Choose button (a real button, so the keyboard works), or paste it. The picker
// offers only the accepted types. Whatever arrives is handed to onSelect, and the caller checks it.
import { DropZone as AriaDropZone, FileTrigger, isFileDropItem, Text } from 'react-aria-components'
import { Button } from '@/components/Button/Button.tsx'
import { Icon } from '@/components/Icon/Icon.tsx'
import styles from './DropZone.module.css'

type DropZoneProps = {
  title: string
  hint?: string
  buttonLabel: string
  acceptedFileTypes: string[]
  onSelect: (files: File[]) => void
  errorMessage?: string
}

export function DropZone({ title, hint, buttonLabel, acceptedFileTypes, onSelect, errorMessage }: DropZoneProps) {
  return (
    <div className={styles.wrapper}>
      <AriaDropZone
        className={`${styles.zone} ${errorMessage ? styles.error : ''}`}
        getDropOperation={(types) => (acceptedFileTypes.some((type) => types.has(type)) ? 'copy' : 'cancel')}
        onDrop={async (event) => {
          const files = await Promise.all(event.items.filter(isFileDropItem).map((item) => item.getFile()))
          onSelect(files)
        }}
      >
        <Icon name={errorMessage ? 'cloud_off' : 'cloud_upload'} />
        <Text slot="label" className={styles.title}>
          {title}
        </Text>
        {hint && <span className={styles.hint}>{hint}</span>}
        <FileTrigger acceptedFileTypes={acceptedFileTypes} onSelect={(files) => files && onSelect([...files])}>
          <Button variant="secondary">
            {buttonLabel}
          </Button>
        </FileTrigger>
      </AriaDropZone>
      {errorMessage && (
        <p role="alert" className={styles.message}>
          <Icon name="error" />
          {errorMessage}
        </p>
      )}
    </div>
  )
}
