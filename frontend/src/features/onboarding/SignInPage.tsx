// The sign-in page, a stub until the onboarding branch builds the landing. Its button signs in with
// Microsoft, so sign-in keeps working until then, and a refused sign-in still says why.
import { Button } from '@/components/actions/Button/Button.tsx'
import { Logo } from '@/components/brand/Logo/Logo.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { useAuth } from '@/lib/auth/useAuth.ts'
import { pageNames } from '@/lib/copy.ts'

export function SignInPage() {
  const { signIn, error } = useAuth()
  return (
    <>
      <PageHeader title={pageNames.signIn} />
      <Button variant="sign-in" onPress={() => void signIn()}>
        <Logo variant="microsoft" />
        Continue with UCT Email
      </Button>
      {error && <p role="alert">Sign-in failed: {error}</p>}
    </>
  )
}
