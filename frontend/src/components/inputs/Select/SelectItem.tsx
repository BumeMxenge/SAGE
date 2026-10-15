// One option of a Select: a name, an optional second line such as its course codes, and an optional
// figure on the right such as its credits. The id is the key the Select reports when it is chosen.
import { ListBoxItem, Text } from 'react-aria-components'
import styles from '@/components/overlays/Popover/Popover.module.css'

type SelectItemProps = { id: string; description?: string; detail?: string; children: string }

export function SelectItem({ id, description, detail, children }: SelectItemProps) {
  return (
    <ListBoxItem id={id} textValue={children} className={`${styles.item} ${styles.option}`}>
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
      {detail && <span className={styles.detail}>{detail}</span>}
    </ListBoxItem>
  )
}
