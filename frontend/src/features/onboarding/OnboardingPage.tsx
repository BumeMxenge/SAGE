// Onboarding: Account Created, then the transcript upload and its review. The steps live in this
// page's state: nothing is saved until Finish Setup, and a reload reads the transcript again, so no
// step needs an address of its own.
import { useState } from 'react'
import { Logo } from '@/components/brand/Logo/Logo.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { AccountCreated } from '@/features/onboarding/components/AccountCreated/AccountCreated.tsx'
import { OnboardingSteps } from '@/features/onboarding/components/OnboardingSteps/OnboardingSteps.tsx'
import { UploadStep } from '@/features/onboarding/components/UploadStep/UploadStep.tsx'
import type { components } from '@/lib/api-types.ts'
import { pageNames } from '@/lib/copy.ts'
import styles from './OnboardingPage.module.css'

type Step =
  | { name: 'welcome' }
  | { name: 'upload' }
  | { name: 'review'; transcript: components['schemas']['Transcript'] }

export function OnboardingPage() {
  const [step, setStep] = useState<Step>({ name: 'welcome' })
  if (step.name === 'welcome') return <AccountCreated onNext={() => setStep({ name: 'upload' })} />
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <Logo variant="compact" />
        <OnboardingSteps current={step.name} />
      </header>
      {/* Each step takes focus as it opens, so a screen reader starts reading it from its heading */}
      <main key={step.name} ref={(main) => main?.focus()} tabIndex={-1} className={styles.main}>
        {step.name === 'upload' ? (
          <UploadStep onContinue={(transcript) => setStep({ name: 'review', transcript })} />
        ) : (
          // The stub's heading, until the review takes its place
          <PageHeader title={pageNames.onboarding} />
        )}
      </main>
    </div>
  )
}
