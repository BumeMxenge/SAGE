// The chat box: a rounded box holding the text and a round Send button on the right. It starts one
// line tall and grows with the text, up to five lines. Enter sends, and Shift+Enter starts a new line.
// Send stays grey until there is something to send. Clicking in shows no highlight, as in the
// prototype; the focus ring appears only when the box is reached with the keyboard.
import { type KeyboardEvent, useState } from 'react'
import { Button, Label, TextArea, TextField } from 'react-aria-components'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import styles from './ChatBox.module.css'

type ChatBoxProps = { label: string; placeholder: string; onSend: (message: string) => void }

export function ChatBox({ label, placeholder, onSend }: ChatBoxProps) {
  const [draft, setDraft] = useState('')
  const message = draft.trim()

  function send() {
    if (!message) return
    onSend(message)
    setDraft('')
  }

  function sendOnEnter(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      send()
    }
  }

  return (
    <form
      className={styles.chatBox}
      onSubmit={(event) => {
        event.preventDefault()
        send()
      }}
    >
      <TextField value={draft} onChange={setDraft} className={styles.field}>
        <Label className="visually-hidden">{label}</Label>
        {/* The hidden copy of the text sizes the box, so it grows without any script */}
        <div className={styles.grow} data-value={draft}>
          <TextArea rows={1} placeholder={placeholder} onKeyDown={sendOnEnter} className={styles.textarea} />
        </div>
      </TextField>
      <Button type="submit" aria-label="Send" isDisabled={!message} className={styles.send}>
        <Icon name="arrow_upward" />
      </Button>
    </form>
  )
}
