// Onboarding: Account Created, then the transcript upload and its review. The steps live in this
// page's state: nothing is saved until Finish Setup, and a reload reads the transcript again, so no
// step needs an address of its own.
import { usePrefetchQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { Logo } from '@/components/brand/Logo/Logo.tsx'
import { AccountCreated } from '@/features/onboarding/components/AccountCreated/AccountCreated.tsx'
import { OnboardingSteps } from '@/features/onboarding/components/OnboardingSteps/OnboardingSteps.tsx'
import { ReviewStep } from '@/features/onboarding/components/ReviewStep/ReviewStep.tsx'
import { UploadStep } from '@/features/onboarding/components/UploadStep/UploadStep.tsx'
import { focusOnOpen } from '@/features/onboarding/focusOnOpen.ts'
import type { components } from '@/lib/api-types.ts'
import { queries, refresh } from '@/lib/queryKeys.ts'
import styles from './OnboardingPage.module.css'

type Step =
  | { name: 'welcome' }
  | { name: 'upload' }
  | { name: 'review'; transcript: components['schemas']['Transcript'] }

export function OnboardingPage() {
  const [step, setStep] = useState<Step>({ name: 'welcome' })
  const navigate = useNavigate()
  // The review needs the catalogue, so its read starts now, while the student uploads
  usePrefetchQuery(queries.catalogue())

  // Finish Setup completed the account: what it changed is read again, and the student's plans open
  async function finished() {
    await refresh.setupFinished()
    await navigate('/plan', { replace: true })
  }

  if (step.name === 'welcome') return <AccountCreated onNext={() => setStep({ name: 'upload' })} />
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <Logo variant="compact" />
        <OnboardingSteps current={step.name} />
      </header>
      {/* Each step takes focus as it opens, so a screen reader starts reading it from its heading */}
      <main key={step.name} ref={focusOnOpen} tabIndex={-1} className={styles.main}>
        {step.name === 'upload' ? (
          <UploadStep onContinue={(transcript) => setStep({ name: 'review', transcript })} />
        ) : (
          <ReviewStep transcript={step.transcript} onSaved={finished} />
        )}
      </main>
    </div>
  )
}
