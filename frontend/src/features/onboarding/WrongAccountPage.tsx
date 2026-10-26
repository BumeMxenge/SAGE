// The page that turns away an account SAGE can't serve, which holds only its heading
// (docs/shortfalls.md). Like every onboarding page, it shows light only.
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { useLightOnly } from '@/features/onboarding/useLightOnly.ts'
import { pageNames } from '@/lib/copy.ts'

export function WrongAccountPage() {
  useLightOnly()
  return <PageHeader title={pageNames.wrongAccount} />
}
