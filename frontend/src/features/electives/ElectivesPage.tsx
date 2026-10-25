// Explore Electives: the complementary studies courses, a tab for each category, one card for each
// course. The search filters the cards the page already holds, hiding tabs with no match, and the
// open tab stays in the address. A heart saves as she presses it, and comes back if it doesn't save.
// Nothing shows while the courses are on their way, and a read that fails after its retries shows
// its error where the tabs would be, with Try Again, as the title and the search stay.
import { useQuery } from '@tanstack/react-query'
import { type ReactNode, useState } from 'react'
import { useNavigate } from 'react-router'
import { Button } from '@/components/actions/Button/Button.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { EmptyState } from '@/components/feedback/EmptyState/EmptyState.tsx'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { SearchField } from '@/components/inputs/SearchField/SearchField.tsx'
import { pageNames } from '@/lib/copy.ts'
import { electivesPath, useElectivesAddress } from '@/lib/electivesAddress.ts'
import { actionLabels, explain } from '@/lib/errors.ts'
import { queries } from '@/lib/queryKeys.ts'
import { keeping, matches, openingTab } from './cards.ts'
import { CategoryTabs } from './components/CategoryTabs/CategoryTabs.tsx'
import { ElectiveCard } from './components/ElectiveCard/ElectiveCard.tsx'
import { noMatch, noMatchMessage, searchPlaceholder } from './copy.ts'
import { useHearting } from './useHearting.ts'
import styles from './ElectivesPage.module.css'

export function ElectivesPage() {
  const address = useElectivesAddress()
  const navigate = useNavigate()
  const electives = useQuery(queries.electives())
  const hearting = useHearting()
  const [search, setSearch] = useState('')

  let body: ReactNode = null
  if (electives.error) {
    const { title, message, reference } = explain(electives.error)
    body = (
      <ErrorState variant="region" tone="danger" icon="error" title={title} message={message} reference={reference}>
        <Button variant="secondary" onPress={() => void electives.refetch()}>
          {actionLabels.retry}
        </Button>
      </ErrorState>
    )
  } else if (electives.data) {
    const shown = keeping(electives.data.tabs, (card) => matches(card, search))
    // Searching opens the first tab with a match without changing the address, so clearing the
    // search goes back to her tab
    const selected = openingTab(shown, address.tab)
    body =
      selected === null ? (
        <EmptyState title={noMatch} message={noMatchMessage(search)} />
      ) : (
        <CategoryTabs
          tabs={shown}
          selected={selected}
          onSelect={(tab) => void navigate(electivesPath({ ...address, tab }), { replace: true })}
        >
          {(tab) =>
            tab.courses.map((card) => (
              <ElectiveCard key={card.codes[0]} card={card} onHeartChange={(heart) => hearting.mutate({ card, heart })} />
            ))
          }
        </CategoryTabs>
      )
  }

  return (
    <div className={styles.page}>
      <PageHeader title={pageNames.electives} />
      <SearchField
        label="Search Electives"
        placeholder={searchPlaceholder}
        value={search}
        onChange={setSearch}
        isDisabled={electives.isError}
      />
      {body}
    </div>
  )
}
