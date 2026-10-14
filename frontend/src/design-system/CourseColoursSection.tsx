import { Section } from '@/design-system/Section.tsx'
import { colourValue, ratio, tokensWithPrefix, type Theme } from '@/lib/tokens.ts'
import styles from './DesignSystem.module.css'

export function CourseColoursSection({ tokens, theme }: { tokens: Map<string, string>; theme: Theme }) {
  return (
    <Section
      title="Course Colours"
      intro="The timetable gives these out in order: teal, orange, navy, pink, blue, ochre, purple, dark teal. Each carries white text, so each needs 4.5:1 against white."
    >
      <div className={styles.samples}>
        {tokensWithPrefix(tokens, '--color-course-').map(([name]) => {
          const value = ratio(tokens, '--color-on-fill', name, theme)
          return (
            <div key={name} className={styles.courseBlock} style={{ '--sample': `var(${name})` }}>
              <span className={styles.courseCode}>Course code</span>
              <span>Start and end time</span>
              <span>
                {colourValue(tokens, name, theme)}, white on it {value.toFixed(2)}:1 ({value >= 4.5 ? 'Pass' : 'Fail'})
              </span>
            </div>
          )
        })}
      </div>
    </Section>
  )
}
