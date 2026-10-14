import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import { tokensWithPrefix } from '@/lib/tokens.ts'
import styles from './DesignSystem.module.css'

export function RadiiSection({ tokens }: { tokens: Map<string, string> }) {
  return (
    <Section title="Corner Radii" intro="Four corner sizes and a full pill.">
      <div className={styles.samples}>
        {tokensWithPrefix(tokens, '--radius-').map(([name, value]) => (
          <Sample key={name} label={`${name}: ${value}`}>
            <div className={styles.radiusBox} style={{ '--sample': `var(${name})` }} />
          </Sample>
        ))}
      </div>
    </Section>
  )
}
