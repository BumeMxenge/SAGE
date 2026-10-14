// A one-line text field. Every field has a label: labelHidden keeps it for screen readers where the
// design shows none. The description and the error message sit below the field.
import { FieldError, Input, Label, Text, TextField as AriaTextField, type TextFieldProps as AriaTextFieldProps } from 'react-aria-components'
import styles from './TextField.module.css'

type TextFieldProps = Omit<AriaTextFieldProps, 'className' | 'style' | 'children'> & {
  label: string
  labelHidden?: boolean
  description?: string
  errorMessage?: string
  placeholder?: string
}

export function TextField({ label, labelHidden, description, errorMessage, placeholder, ...props }: TextFieldProps) {
  return (
    <AriaTextField {...props} className={styles.field}>
      <Label className={labelHidden ? 'visually-hidden' : styles.label}>{label}</Label>
      <Input className={styles.input} placeholder={placeholder} />
      {description && (
        <Text slot="description" className={styles.description}>
          {description}
        </Text>
      )}
      <FieldError className={styles.error}>{errorMessage}</FieldError>
    </AriaTextField>
  )
}
