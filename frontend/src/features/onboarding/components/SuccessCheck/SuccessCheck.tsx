// The tick that greets a new account: Material's check on a round accent tile. It scales and fades in
// once; under reduced motion it is simply there. The greeting beside it says the same, so screen
// readers skip it.
import { Icon } from '@/components/brand/Icon/Icon.tsx'
import styles from './SuccessCheck.module.css'

export function SuccessCheck() {
  return (
    <span aria-hidden="true" className={styles.successCheck}>
      <Icon name="check" />
    </span>
  )
}
