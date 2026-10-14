import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import { useMediaQuery } from '@/design-system/useMediaQuery.ts'
import { type Tokens, tokensWithPrefix } from '@/lib/tokens.ts'
import styles from './DesignSystem.module.css'

export function MotionSection({ tokens }: { tokens: Tokens }) {
  const reduced = useMediaQuery('(prefers-reduced-motion: reduce)')
  return (
    <Section
      title="Motion"
      intro={`Two durations, one easing and two loop periods. With reduced motion on, every duration is 0 and the dots below stand still. Reduced motion is ${reduced ? 'on' : 'off'} now.`}
    >
      <div className={styles.samples}>
        {tokensWithPrefix(tokens, '--duration-').map(([name, value]) => (
          <Sample key={name} label={`${name}: ${value}`}>
            <div className={styles.motionTrack}>
              <div className={styles.motionDot} style={{ '--sample': `var(${name})` }} />
            </div>
          </Sample>
        ))}
      </div>
      <p className={styles.intro}>Easing: {tokens.light.get('--easing')}</p>
    </Section>
  )
}
