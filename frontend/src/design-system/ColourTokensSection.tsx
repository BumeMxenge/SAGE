import { DataTable } from '@/components/DataTable/DataTable.tsx'
import { Section } from '@/design-system/Section.tsx'
import { contrastChecks, ratio, type Theme, type Tokens, tokenValue } from '@/lib/tokens.ts'
import styles from './DesignSystem.module.css'

export function ColourTokensSection({ tokens, theme }: { tokens: Tokens; theme: Theme }) {
  const checks = contrastChecks(tokens)
  const names = [...tokens.light.keys()].filter((name) => name.startsWith('--color-') && !name.startsWith('--color-course-'))
  const rows = names.map((name) => ({
    id: name,
    cells: {
      token: <code>{name}</code>,
      swatch: <span className={styles.swatch} style={{ '--sample': `var(${name})` }} />,
      light: tokenValue(tokens, name, 'light'),
      dark: tokenValue(tokens, name, 'dark'),
      contrast: (
        <ul className={styles.list}>
          {checks
            .filter((check) => check.token === name)
            .flatMap((check) =>
              check.against.map((against) => {
                const value = ratio(tokens, name, against, theme)
                return (
                  <li key={against}>
                    {value.toFixed(2)}:1 on <code>{against}</code>: {value >= check.minimum ? 'Pass' : 'Fail'} (needs {check.minimum}:1)
                  </li>
                )
              }),
            )}
        </ul>
      ),
    },
  }))
  return (
    <Section
      title="Colour Tokens"
      intro="Each colour with its light value (theme.css, first block) and dark value (second block), or one value from tokens.css when both themes share it, and its contrast against every surface it sits on, in the theme now on screen. Text needs 4.5:1, and the input border and focus ring need 3:1. Colours with no ratio are surfaces, fills or decoration."
    >
      <DataTable
        caption={`Colour tokens, ratios in the ${theme} theme`}
        columns={[
          { key: 'token', header: 'Token' },
          { key: 'swatch', header: 'Now' },
          { key: 'light', header: 'Light' },
          { key: 'dark', header: 'Dark' },
          { key: 'contrast', header: 'Contrast' },
        ]}
        rows={rows}
        emptyMessage="No colour tokens found."
      />
    </Section>
  )
}
