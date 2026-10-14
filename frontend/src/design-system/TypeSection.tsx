import { DataTable } from '@/components/DataTable/DataTable.tsx'
import { Section } from '@/design-system/Section.tsx'
import { tokensWithPrefix } from '@/lib/tokens.ts'
import styles from './DesignSystem.module.css'

export function TypeSection({ tokens }: { tokens: Map<string, string> }) {
  const sizes = tokensWithPrefix(tokens, '--font-size-').map(([name, value]) => ({
    id: name,
    cells: {
      token: <code>{name}</code>,
      value,
      sample: (
        <span className={styles.typeSample} style={{ '--sample': `var(${name})` }}>
          Registration, without the guesswork
        </span>
      ),
    },
  }))
  const weights = tokensWithPrefix(tokens, '--font-weight-').map(([name, value]) => ({
    id: name,
    cells: {
      token: <code>{name}</code>,
      value,
      sample: (
        <span className={styles.weightSample} style={{ '--sample': `var(${name})` }}>
          Registration, without the guesswork
        </span>
      ),
    },
  }))
  const columns = [
    { key: 'token', header: 'Token' },
    { key: 'value', header: 'Value' },
    { key: 'sample', header: 'Sample' },
  ]
  return (
    <Section title="Type" intro="Inter Variable in seven sizes, from 12 px, the smallest text allowed, to 30 px, and three weights.">
      <DataTable caption="Type sizes" columns={columns} rows={sizes} emptyMessage="No sizes." />
      <DataTable caption="Type weights" columns={columns} rows={weights} emptyMessage="No weights." />
    </Section>
  )
}
