// The onboarding page, a stub until the onboarding branch builds the transcript upload and review
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { pageNames } from '@/lib/copy.ts'

export function OnboardingPage() {
  return <PageHeader title={pageNames.onboarding} />
}
