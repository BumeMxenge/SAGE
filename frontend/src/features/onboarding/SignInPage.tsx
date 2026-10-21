// The sign-in landing: SAGE's promise and the one button that signs in with Microsoft, new and
// returning students alike, beside three highlights of what SAGE does
import { Button } from '@/components/actions/Button/Button.tsx'
import { Logo } from '@/components/brand/Logo/Logo.tsx'
import { BrandShapes } from '@/features/onboarding/components/BrandShapes/BrandShapes.tsx'
import { Highlights } from '@/features/onboarding/components/Highlights/Highlights.tsx'
import { useLightOnly } from '@/features/onboarding/useLightOnly.ts'
import { useAuth } from '@/lib/auth/useAuth.ts'
import styles from './SignInPage.module.css'

export function SignInPage() {
  useLightOnly()
  const { signIn } = useAuth()
  return (
    <main className={styles.page}>
      <div className={styles.form}>
        <Logo variant="compact" />
        <div className={styles.content}>
          <h1 className={styles.headline}>
            <span className={styles.accent}>Registration,</span> <span>without the guesswork.</span>
          </h1>
          <p className={styles.lead}>Your courses, your rules, your clashes, all sorted in one place.</p>
          <Button variant="sign-in" onPress={() => void signIn()}>
            <Logo variant="microsoft" />
            Continue with UCT Email
          </Button>
          <p className={styles.helper}>
            Sign in with your UCT Microsoft account. New and returning students use the same button.
          </p>
        </div>
        <p className={styles.legal}>
          By continuing you agree to our <a href="/privacy.html">Privacy Policy</a>.
        </p>
      </div>
      <div className={styles.panel}>
        <BrandShapes layout="sign-in" />
        <Highlights />
      </div>
    </main>
  )
}
