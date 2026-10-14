// The SAGE leaf, its three petals pulsing in turn, beside a status line such as "Building your plans".
// The words are always there. Under reduced motion the leaf stands still.
import { Logo } from '@/components/Logo/Logo.tsx'
import styles from './LeafPulse.module.css'

export function LeafPulse({ label }: { label: string }) {
  return (
    <output className={styles.leafPulse}>
      <span aria-hidden="true" className={styles.leaf}>
        <Logo variant="mark" />
      </span>
      {label}
    </output>
  )
}
