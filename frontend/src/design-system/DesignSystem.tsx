// The review page: every token and shared component, each in its states, so the design can be checked
// against the prototypes in both themes. Development only. It also serves as evidence for Chapter 4.
import { PageHeader } from '@/components/PageHeader/PageHeader.tsx'
import { Segment } from '@/components/SegmentedControl/Segment.tsx'
import { SegmentedControl } from '@/components/SegmentedControl/SegmentedControl.tsx'
import { ToastRegion } from '@/components/ToastRegion/ToastRegion.tsx'
import { ButtonsSection } from '@/design-system/ButtonsSection.tsx'
import { ChoicesSection } from '@/design-system/ChoicesSection.tsx'
import { ColourTokensSection } from '@/design-system/ColourTokensSection.tsx'
import { ContentSection } from '@/design-system/ContentSection.tsx'
import { CourseColoursSection } from '@/design-system/CourseColoursSection.tsx'
import { IconsSection } from '@/design-system/IconsSection.tsx'
import { LoadingSection } from '@/design-system/LoadingSection.tsx'
import { LogosSection } from '@/design-system/LogosSection.tsx'
import { MotionSection } from '@/design-system/MotionSection.tsx'
import { OverlaysSection } from '@/design-system/OverlaysSection.tsx'
import { RadiiSection } from '@/design-system/RadiiSection.tsx'
import { ShadowsSection } from '@/design-system/ShadowsSection.tsx'
import { SpacingSection } from '@/design-system/SpacingSection.tsx'
import { FieldsSection } from '@/design-system/FieldsSection.tsx'
import { TypeSection } from '@/design-system/TypeSection.tsx'
import { useResolvedTheme } from '@/design-system/useResolvedTheme.ts'
import { parseTokens } from '@/lib/tokens.ts'
import { type Appearance, useAppearance } from '@/lib/useAppearance.ts'
import themeCss from '@/styles/theme.css?raw'
import tokensCss from '@/styles/tokens.css?raw'
import styles from './DesignSystem.module.css'

const tokens = parseTokens(tokensCss, themeCss)
const appearances: { id: Appearance; label: string }[] = [
  { id: 'system', label: 'Match System' },
  { id: 'light', label: 'Light' },
  { id: 'dark', label: 'Dark' },
]

export function DesignSystem() {
  const { appearance, choose } = useAppearance()
  const theme = useResolvedTheme(appearance)
  return (
    <>
      <main className={styles.page}>
        <PageHeader
          title="SAGE Design System"
          subtitle="Every token and shared component, in each state the prototypes draw. Change the appearance to check both themes. Onboarding is designed in light only."
          actions={
            <SegmentedControl
              label="Appearance"
              selectedKey={appearance}
              onChange={(key) => {
                const chosen = appearances.find((option) => option.id === key)
                if (chosen) choose(chosen.id)
              }}
            >
              {appearances.map((option) => (
                <Segment key={option.id} id={option.id}>
                  {option.label}
                </Segment>
              ))}
            </SegmentedControl>
          }
        />
        <ColourTokensSection tokens={tokens} theme={theme} />
        <CourseColoursSection tokens={tokens} theme={theme} />
        <TypeSection tokens={tokens} />
        <SpacingSection tokens={tokens} />
        <RadiiSection tokens={tokens} />
        <ShadowsSection tokens={tokens} />
        <MotionSection tokens={tokens} />
        <IconsSection />
        <LogosSection />
        <ButtonsSection />
        <ChoicesSection />
        <FieldsSection />
        <OverlaysSection />
        <LoadingSection />
        <ContentSection />
      </main>
      <ToastRegion />
    </>
  )
}
