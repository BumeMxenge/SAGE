// The first step of onboarding: the account exists, so SAGE welcomes the student and sends them on to
// their course history. The greeting uses the name Microsoft gave this browser, if any (approved
// difference 14), and waits until sign-in has said, so the name never appears late.
import { Button } from '@/components/actions/Button/Button.tsx'
import { Logo } from '@/components/brand/Logo/Logo.tsx'
import { BrandShapes } from '@/features/onboarding/components/BrandShapes/BrandShapes.tsx'
import { Confetti } from '@/features/onboarding/components/Confetti/Confetti.tsx'
import { SuccessCheck } from '@/features/onboarding/components/SuccessCheck/SuccessCheck.tsx'
import { useAuth } from '@/lib/auth/useAuth.ts'
import styles from './AccountCreated.module.css'

export function AccountCreated({ onNext }: { onNext: () => void }) {
  const { name, loading } = useAuth()
  return (
    <main className={styles.page}>
      <BrandShapes layout="account-created" />
      <Confetti />
      <div className={styles.logo}>
        <Logo variant="compact" />
      </div>
      <div className={styles.content}>
        <SuccessCheck />
        {!loading && (
          <h1 className={styles.greeting}>
            {name ? (
              <>
                <span className={styles.accent}>You're in,</span> {name.givenName}.
              </>
            ) : (
              <span className={styles.accent}>You're in.</span>
            )}
          </h1>
        )}
        <Button variant="sign-in" onPress={onNext}>
          Next, Your Course History
        </Button>
        <p className={styles.time}>Takes about two minutes</p>
      </div>
    </main>
  )
}
