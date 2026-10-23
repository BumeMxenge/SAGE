// The chat box: a rounded box holding the text and a round Send button on the right. It starts one
// line tall and grows with the text, up to five lines. Enter sends, and Shift+Enter starts a new line.
// Send stays grey until there is something to send, and while a reply is on its way, when Enter sends
// nothing either, though the next question can still be typed. Clicking in shows no highlight, as in
// the prototype; the focus ring appears only when the box is reached with the keyboard. The ref
// reaches the text area, so the assistant can move focus into it.
import { type KeyboardEvent, type Ref, useState } from 'react'
import { Button, Label, TextArea, TextField } from 'react-aria-components'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import styles from './ChatBox.module.css'

// The API's limit for a question
const longest = 2000

type ChatBoxProps = {
  label: string
  placeholder: string
  waiting: boolean
  onSend: (message: string) => void
  ref?: Ref<HTMLTextAreaElement>
}

export function ChatBox({ label, placeholder, waiting, onSend, ref }: ChatBoxProps) {
  const [draft, setDraft] = useState('')
  const message = draft.trim()
  const ready = message !== '' && !waiting

  function send() {
    if (!ready) return
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
      <TextField value={draft} onChange={setDraft} maxLength={longest} className={styles.field}>
        <Label className="visually-hidden">{label}</Label>
        {/* The hidden copy of the text sizes the box, so it grows without any script */}
        <div className={styles.grow} data-value={draft}>
          <TextArea ref={ref} rows={1} placeholder={placeholder} onKeyDown={sendOnEnter} className={styles.textarea} />
        </div>
      </TextField>
      <Button type="submit" aria-label="Send" isDisabled={!ready} className={styles.send}>
        <Icon name="arrow_upward" />
      </Button>
    </form>
  )
}
