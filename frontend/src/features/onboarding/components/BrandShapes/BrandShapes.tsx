// The large shapes in the logo's colours behind the sign-in highlights and Account Created: circles, a
// petal and a faint ring. They are decoration only, so screen readers skip them.
import styles from './BrandShapes.module.css'

export function BrandShapes({ layout }: { layout: 'sign-in' | 'account-created' }) {
  return (
    <div aria-hidden="true" className={styles.shapes} data-layout={layout}>
      {layout === 'sign-in' && <span className={styles.coral} />}
      <span className={styles.teal} />
      <span className={styles.petal} />
      <span className={styles.ring} />
    </div>
  )
}
