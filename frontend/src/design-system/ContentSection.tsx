import { Badge } from '@/components/Badge/Badge.tsx'
import { Button } from '@/components/Button/Button.tsx'
import { Card } from '@/components/Card/Card.tsx'
import { DataTable } from '@/components/DataTable/DataTable.tsx'
import { EmptyState } from '@/components/EmptyState/EmptyState.tsx'
import { ErrorState } from '@/components/ErrorState/ErrorState.tsx'
import { ToggleButton } from '@/components/ToggleButton/ToggleButton.tsx'
import { Sample } from '@/design-system/Sample.tsx'
import { Section } from '@/design-system/Section.tsx'
import styles from './DesignSystem.module.css'

const columns = [
  { key: 'code', header: 'Code' },
  { key: 'name', header: 'Course' },
  { key: 'credits', header: 'Credits', align: 'end' as const },
]

export function ContentSection() {
  return (
    <Section
      title="Content"
      intro="Tables, cards, badges and the states a region shows when it is empty or has failed. The page header is the one at the top of this page: it is the only way a page gets its h1."
    >
      <div className={styles.samples}>
        <Sample label="Data table: with rows, and empty">
          <div className={styles.wide}>
            <DataTable
              caption="2025 · Example Year"
              columns={columns}
              rows={[
                { id: 'a', cells: { code: 'ABC1001F', name: 'Example Course One', credits: '16' } },
                { id: 'b', cells: { code: 'ABC1002S', name: 'Example Course Two', credits: '24' } },
              ]}
              emptyMessage="No courses yet."
            />
          </div>
          <div className={styles.wide}>
            <DataTable caption="2026 · Example Year" columns={columns} rows={[]} emptyMessage="No courses yet." />
          </div>
        </Sample>
        <Sample label="Card: with an action">
          <div className={styles.narrow}>
            <Card title="Example Elective" actions={<ToggleButton label="Favourite ABC1001F" />}>
              <Badge tone="accent">Eligible</Badge>
              <p>One or two sentences about the course, from its summary.</p>
            </Card>
          </div>
        </Sample>
        <Sample label="Badges: neutral, accent, warning, danger">
          <Badge>ABC1001F</Badge>
          <Badge tone="accent">Eligible</Badge>
          <Badge tone="warning">Check With Your Advisor</Badge>
          <Badge tone="danger">Not Eligible</Badge>
        </Sample>
        <Sample label="Empty state">
          <EmptyState
            title="Build Your 2026 Plan"
            message="Answer a few questions and SAGE shows the plans that fit."
            action={<Button>Create Registration Plan</Button>}
          />
        </Sample>
        <Sample label="Error state">
          <ErrorState
            title="Account Can't Use SAGE"
            message="SAGE is for UCT students. Sign out and try your student email."
            action={<Button variant="secondary">Sign Out</Button>}
          />
        </Sample>
      </div>
    </Section>
  )
}
