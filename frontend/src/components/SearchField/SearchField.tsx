// A search box with a magnifier and a clear button. The clear button shows only once something is typed.
import { Button, FieldError, Input, Label, SearchField as AriaSearchField, type SearchFieldProps as AriaSearchFieldProps, Text } from 'react-aria-components'
import { Icon } from '@/components/Icon/Icon.tsx'
import fieldStyles from '@/components/TextField/TextField.module.css'
import styles from './SearchField.module.css'

type SearchFieldProps = Omit<AriaSearchFieldProps, 'className' | 'style' | 'children'> & {
  label: string
  labelHidden?: boolean
  description?: string
  errorMessage?: string
  placeholder?: string
}

export function SearchField({ label, labelHidden, description, errorMessage, placeholder, ...props }: SearchFieldProps) {
  return (
    <AriaSearchField {...props} className={`${fieldStyles.field} ${styles.searchField}`}>
      <Label className={labelHidden ? 'visually-hidden' : fieldStyles.label}>{label}</Label>
      <div className={styles.box}>
        <span className={styles.icon}>
          <Icon name="search" />
        </span>
        <Input className={fieldStyles.input} placeholder={placeholder} />
        <Button className={styles.clear}>
          <Icon name="close" />
        </Button>
      </div>
      {description && (
        <Text slot="description" className={fieldStyles.description}>
          {description}
        </Text>
      )}
      <FieldError className={fieldStyles.error}>{errorMessage}</FieldError>
    </AriaSearchField>
  )
}
