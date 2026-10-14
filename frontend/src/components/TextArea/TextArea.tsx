// A text field for several lines, such as the chat box. It looks like TextField and grows when the
// student drags its corner.
import { FieldError, Label, Text, TextArea as AriaTextArea, TextField as AriaTextField, type TextFieldProps as AriaTextFieldProps } from 'react-aria-components'
import styles from '@/components/TextField/TextField.module.css'
import areaStyles from './TextArea.module.css'

type TextAreaProps = Omit<AriaTextFieldProps, 'className' | 'style' | 'children'> & {
  label: string
  labelHidden?: boolean
  description?: string
  errorMessage?: string
  placeholder?: string
  rows?: number
}

export function TextArea({ label, labelHidden, description, errorMessage, placeholder, rows = 3, ...props }: TextAreaProps) {
  return (
    <AriaTextField {...props} className={styles.field}>
      <Label className={labelHidden ? 'visually-hidden' : styles.label}>{label}</Label>
      <AriaTextArea className={`${styles.input} ${areaStyles.textarea}`} placeholder={placeholder} rows={rows} />
      {description && (
        <Text slot="description" className={styles.description}>
          {description}
        </Text>
      )}
      <FieldError className={styles.error}>{errorMessage}</FieldError>
    </AriaTextField>
  )
}
