// Who is signed in: an avatar beside a name and a second line. The sidebar's account button and the
// account menu's header show the student this way. The avatar shows initials, or a person icon when
// Microsoft gave no name (approved difference 14). It is made of spans, so it may sit inside a
// button, as the account button holds it.
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import styles from './Account.module.css'

type AccountProps = { name: string; detail: string; initials?: string }

export function Account({ name, detail, initials }: AccountProps) {
  return (
    <span className={styles.account}>
      <span aria-hidden="true" className={styles.avatar}>
        {initials ?? <Icon name="person" />}
      </span>
      <span className={styles.text}>
        <span className={styles.name}>{name}</span>
        <span className={styles.detail}>{detail}</span>
      </span>
    </span>
  )
}
