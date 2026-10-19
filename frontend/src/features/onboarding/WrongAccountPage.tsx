// The page that turns away an account SAGE can't serve, a stub until the onboarding branch builds it.
// Like every onboarding page, it shows light only.
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { useLightOnly } from '@/features/onboarding/useLightOnly.ts'
import { pageNames } from '@/lib/copy.ts'

export function WrongAccountPage() {
  useLightOnly()
  return <PageHeader title={pageNames.wrongAccount} />
}
