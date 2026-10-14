import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import { tokensWithPrefix } from '@/lib/tokens.ts'
import styles from './DesignSystem.module.css'

export function SpacingSection({ tokens }: { tokens: Map<string, string> }) {
  return (
    <Section title="Spacing" intro="A 4 px scale. Every gap, padding and margin is one of these.">
      <div className={styles.samples}>
        {tokensWithPrefix(tokens, '--space-').map(([name, value]) => (
          <Sample key={name} label={`${name}: ${value}`}>
            <div className={styles.spaceBar} style={{ '--sample': `var(${name})` }} />
          </Sample>
        ))}
      </div>
    </Section>
  )
}
