import { LeafPulse } from '@/components/LeafPulse/LeafPulse.tsx'
import { ProgressBar } from '@/components/ProgressBar/ProgressBar.tsx'
import { Skeleton } from '@/components/Skeleton/Skeleton.tsx'
import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import styles from './DesignSystem.module.css'

export function LoadingSection() {
  return (
    <Section
      title="Loading"
      intro="Everything that moves has its words beside it, and stands still when the system asks for reduced motion."
    >
      <div className={styles.samples}>
        <Sample label="Progress bar, light only">
          <div className={styles.narrow}>
            <ProgressBar label="Reading your transcript" value={40} />
          </div>
        </Sample>
        <Sample label="Skeleton: line, title, block">
          <div className={styles.narrow}>
            <Skeleton variant="line" />
          </div>
          <div className={styles.narrow}>
            <Skeleton variant="title" />
          </div>
          <div className={styles.fillHeight}>
            <Skeleton variant="block" />
          </div>
        </Sample>
        <Sample label="Leaf pulse: building plans, and the assistant thinking">
          <LeafPulse label="Building your plans" />
        </Sample>
      </div>
    </Section>
  )
}
