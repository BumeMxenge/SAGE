// The chat box: a text area with a placeholder and no visible label. The label is still there for
// screen readers.
import { Label, TextArea as AriaTextArea, TextField, type TextFieldProps } from 'react-aria-components'
import styles from './TextArea.module.css'

type TextAreaProps = Pick<TextFieldProps, 'value' | 'defaultValue' | 'onChange' | 'name'> & {
  label: string
  placeholder: string
  rows?: number
}

export function TextArea({ label, placeholder, rows = 1, ...props }: TextAreaProps) {
  return (
    <TextField {...props} className={styles.field}>
      <Label className="visually-hidden">{label}</Label>
      <AriaTextArea className={styles.textarea} placeholder={placeholder} rows={rows} />
    </TextField>
  )
}
