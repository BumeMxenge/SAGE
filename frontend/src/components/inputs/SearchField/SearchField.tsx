// A search box with a magnifier and a clear button, as on Explore Electives and in the course picker.
// It has a placeholder and no visible label; the label is still there for screen readers. The clear
// button shows only once something is typed.
import { Button, Input, Label, SearchField as AriaSearchField, type SearchFieldProps as AriaSearchFieldProps } from 'react-aria-components'
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import styles from './SearchField.module.css'

type SearchFieldProps = Pick<AriaSearchFieldProps, 'value' | 'defaultValue' | 'onChange' | 'onSubmit' | 'isDisabled'> & {
  label: string
  placeholder: string
}

export function SearchField({ label, placeholder, ...props }: SearchFieldProps) {
  return (
    <AriaSearchField {...props} className={styles.searchField}>
      <Label className="visually-hidden">{label}</Label>
      <span className={styles.icon}>
        <Icon name="search" />
      </span>
      <Input className={styles.input} placeholder={placeholder} />
      <Button className={styles.clear}>
        <Icon name="close" />
      </Button>
    </AriaSearchField>
  )
}
