// Where the student is in setting up: two named steps, each with a bar under it, full once done and
// half full while current. The current step is marked for screen readers too. (ProgressBar would
// announce a percentage, which misdescribes two named steps.)
import styles from './OnboardingSteps.module.css'

const steps = [
  { id: 'upload', name: 'Upload Transcript' },
  { id: 'review', name: 'Review and Verify' },
] as const

export function OnboardingSteps({ current }: { current: (typeof steps)[number]['id'] }) {
  const currentIndex = steps.findIndex((step) => step.id === current)
  return (
    <ol aria-label="Setup steps" className={styles.steps}>
      {steps.map((step, index) => (
        <li
          key={step.id}
          aria-current={index === currentIndex ? 'step' : undefined}
          data-done={index < currentIndex || undefined}
          className={styles.step}
        >
          {step.name}
        </li>
      ))}
    </ol>
  )
}
