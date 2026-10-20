// Who is signed in: an avatar beside a name and a second line. The sidebar's account button and the
// account menu's header show the student this way. The avatar shows initials, or a person icon when
// Microsoft gave no name (approved difference 14). A blocked account, on the page that turns away an
// account that can't use SAGE, is grey and sits in an outlined box. It is made of spans, so it may sit
// inside a button, as the account button holds it.
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import styles from './Account.module.css'

type AccountProps = { name: string; detail: string; initials?: string; blocked?: boolean }

export function Account({ name, detail, initials, blocked = false }: AccountProps) {
  return (
    <span className={styles.account} data-blocked={blocked || undefined}>
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
