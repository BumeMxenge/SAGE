// The page that turns away an account SAGE can't serve, a stub until the onboarding branch builds it
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { pageNames } from '@/lib/copy.ts'

export function WrongAccountPage() {
  return <PageHeader title={pageNames.wrongAccount} />
}
