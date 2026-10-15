import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import { useMediaQuery } from '@/design-system/useMediaQuery.ts'
import type { Tokens } from '@/lib/tokens.ts'
import styles from './DesignSystem.module.css'

// What moves at each speed. Each dot below runs at that speed, so the timing can be felt.
const speeds = [
  {
    token: '--duration-fast',
    use: 'Tooltips, menus and the Select list fade in and out, and a progress bar slides to its new value. The prototypes take 0.12 to 0.16 s for these.',
  },
  {
    token: '--duration-slow',
    use: 'A dialog rises and fades in over its dimmed backdrop. Later screens use it for the sidebar and the assistant opening and closing, and for a page fading in. The prototypes take 0.25 to 0.35 s.',
  },
  { token: '--duration-loop', use: 'One sweep of the shimmer across a loading skeleton, then it starts again.' },
  {
    token: '--duration-loop-slow',
    use: 'One breath of the leaf pulse: the teal, coral and navy petals brighten in turn, a tenth of a breath apart.',
  },
]

export function MotionSection({ tokens }: { tokens: Tokens }) {
  const reduced = useMediaQuery('(prefers-reduced-motion: reduce)')
  return (
    <Section
      title="Motion"
      intro={`Hover changes are instant, as in the prototypes. Everything that moves uses two durations, one easing that starts briskly and settles gently (${tokens.light.get('--easing')}), and two loop periods. With reduced motion on, every duration is 0: the dots stand still, overlays simply appear and the skeleton and leaf hold still. Reduced motion is ${reduced ? 'on' : 'off'} now.`}
    >
      <div className={styles.motionGrid}>
        {speeds.map(({ token, use }) => (
          <Sample key={token} label={`${token}: ${tokens.light.get(token)}. ${use}`}>
            <div className={styles.motionTrack}>
              <div className={styles.motionDot} style={{ '--sample': `var(${token})` }} />
            </div>
          </Sample>
        ))}
      </div>
    </Section>
  )
}
