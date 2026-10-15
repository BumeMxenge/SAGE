import { Account } from '@/components/Account/Account.tsx'
import { Button } from '@/components/Button/Button.tsx'
import { Card } from '@/components/Card/Card.tsx'
import { DataTable } from '@/components/DataTable/DataTable.tsx'
import { EmptyState } from '@/components/EmptyState/EmptyState.tsx'
import { ErrorState } from '@/components/ErrorState/ErrorState.tsx'
import { Logo } from '@/components/Logo/Logo.tsx'
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
      intro="Tables, cards, the signed-in account, and the states a region or page shows when it is empty or has failed. The page header is the one at the top of this page."
    >
      <div className={styles.samples}>
        <Sample label="Data table: a year of course history">
          <div className={styles.wide}>
            <DataTable
              caption="2025 · Example Year"
              columns={columns}
              rows={[
                { id: 'a', cells: { code: 'ABC1001F', name: 'Example Course One', credits: '16' } },
                { id: 'b', cells: { code: 'ABC1002S', name: 'Example Course Two', credits: '24' } },
              ]}
            />
          </div>
        </Sample>
        <Sample label="Card: with an action">
          <div className={styles.narrow}>
            <Card title="Example Elective" actions={<ToggleButton label="Favourite ABC1001F" />}>
              <p>One or two sentences about the course, from its summary.</p>
            </Card>
          </div>
        </Sample>
        <Sample label="Account: the student, as in the sidebar and the account menu, and with no name from Microsoft (approved difference 14)">
          <Account initials="MD" name="Mbali Dlamini" detail="Fourth year · Mechatronics" />
          <Account name="DLMMBA999" detail="Fourth year · Mechatronics" />
        </Sample>
        <Sample label="Empty state: the empty plan">
          <EmptyState
            title="Build Your 2026 Plan"
            message="SAGE starts from your prescribed fourth-year curriculum and your record, then builds only clash-free options for the year."
            action={<Button icon="add">Create Registration Plan</Button>}
          />
        </Sample>
        <Sample label="Error state in a region: error sheet case 06, Saved plan won't load">
          <ErrorState
            variant="region"
            icon="error"
            title="Your Plan Didn't Load"
            message="The registration system didn't respond. Your saved plan hasn't changed."
            reference="SG-7F3A-21C9"
          >
            <Button>Try Again</Button>
          </ErrorState>
        </Sample>
        <Sample label="Error state as a blocking page: error sheet case 02, Account can't use SAGE. Its title is the page's h1, and it is light only, like the rest of onboarding">
          <ErrorState
            variant="page"
            icon="person"
            title="This Account Can't Use SAGE"
            message="SAGE is for registered UCT students. Sign in with your student account, the one ending in @myuct.ac.za."
          >
            <Account blocked initials="MD" name="mbali.dlamini@example.com" detail="Staff account · currently signed in" />
            <Button variant="sign-in">
              <Logo variant="microsoft" />
              Use a Different Account
            </Button>
            <a href="https://icts.uct.ac.za/">Get help from the ICTS service desk</a>
          </ErrorState>
        </Sample>
      </div>
    </Section>
  )
}
