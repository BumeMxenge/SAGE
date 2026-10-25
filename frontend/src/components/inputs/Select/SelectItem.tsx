// One option of a Select: a name, an optional second line such as its course codes, and an optional
// figure on the right such as its credits. All of its text names it, so a screen reader hears what the
// option shows (WCAG 2.5.3). The id is the key the Select reports when it is chosen.
import { ListBoxItem, Text } from 'react-aria-components'
import styles from '@/styles/list.module.css'

type SelectItemProps = { id: string; description?: string; detail?: string; children: string }

export function SelectItem({ id, description, detail, children }: SelectItemProps) {
  return (
    <ListBoxItem id={id} textValue={children} className={`${styles.item} ${styles.option}`}>
      <Text slot="label" className={styles.content}>
        <span className={styles.text}>
          <span className={styles.label}>{children}</span>
          {description && <span className={styles.description}>{description}</span>}
        </span>
        {detail && <span className={styles.detail}>{detail}</span>}
      </Text>
    </ListBoxItem>
  )
}
