// One option of a Select. The id is the key the Select reports when it is chosen.
import { ListBoxItem, Text } from 'react-aria-components'
import styles from '@/components/Popover/Popover.module.css'

type SelectItemProps = { id: string; description?: string; children: string }

export function SelectItem({ id, description, children }: SelectItemProps) {
  return (
    <ListBoxItem id={id} textValue={children} className={styles.item}>
      <span className={styles.text}>
        <Text slot="label" className={styles.label}>
          {children}
        </Text>
        {description && (
          <Text slot="description" className={styles.description}>
            {description}
          </Text>
        )}
      </span>
    </ListBoxItem>
  )
}
