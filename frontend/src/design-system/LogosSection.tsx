import { Logo } from '@/components/Logo/Logo.tsx'
import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import styles from './DesignSystem.module.css'

export function LogosSection() {
  return (
    <Section
      title="Logos"
      intro="Each logo has one fixed height and shows the file that matches the theme, light or dark. Use the appearance switch at the top to see both. The Microsoft mark is Microsoft's own, for the sign-in button."
    >
      <div className={styles.samples}>
        <Sample label="full: sign-in, README and thesis (96 px tall)">
          <Logo variant="full" />
        </Sample>
        <Sample label="compact: sidebar and onboarding header (26 px tall)">
          <Logo variant="compact" />
        </Sample>
        <Sample label="mark: favicon and assistant avatar (28 px tall)">
          <Logo variant="mark" />
        </Sample>
        <Sample label="microsoft: sign-in button (21 px tall)">
          <Logo variant="microsoft" />
        </Sample>
      </div>
    </Section>
  )
}
