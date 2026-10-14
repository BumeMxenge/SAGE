import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import { type Tokens, tokensWithPrefix } from '@/lib/tokens.ts'
import styles from './DesignSystem.module.css'

export function ShadowsSection({ tokens }: { tokens: Tokens }) {
  return (
    <Section title="Shadows" intro="Three elevations. In the dark theme the shadow is 50% black, as measured in the prototypes.">
      <div className={styles.samples}>
        {tokensWithPrefix(tokens, '--shadow-').map(([name]) => (
          <Sample key={name} label={name}>
            <div className={styles.shadowBox} style={{ '--sample': `var(${name})` }} />
          </Sample>
        ))}
      </div>
    </Section>
  )
}
