// Onboarding: Account Created, then the transcript upload and its review. The steps live in this
// page's state: nothing is saved until Finish Setup, and a reload reads the transcript again, so no
// step needs an address of its own.
import { useState } from 'react'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { AccountCreated } from '@/features/onboarding/components/AccountCreated/AccountCreated.tsx'
import { pageNames } from '@/lib/copy.ts'

export function OnboardingPage() {
  const [step, setStep] = useState<'welcome' | 'upload'>('welcome')
  if (step === 'welcome') return <AccountCreated onNext={() => setStep('upload')} />
  // The stub's heading, until the transcript upload takes its place
  return <PageHeader title={pageNames.onboarding} />
}
