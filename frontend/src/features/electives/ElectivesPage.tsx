// Explore Electives: the complementary studies courses, a tab for each category, one card for each
// course. The search filters the cards the page already holds, hiding tabs with no match, and the
// open tab stays in the address. A heart saves as she presses it, and comes back if it doesn't save.
//
// With ?plan=, from a plan's slot card, the page keeps only the courses whose offerings fit that
// plan, as the API lists them, with her favourites first as the page opened, and says which plan.
// A plan that isn't one of hers, or isn't one of her current plans, shows every course and says
// why, and a current plan nothing fits shows its slot's own words.
//
// Nothing shows while a read the page needs is on its way, and a read that fails after its retries
// shows its error where the tabs would be, with Try Again, as the title and the search stay.
import { useQuery } from '@tanstack/react-query'
import { type ReactNode, useState } from 'react'
import { Link } from 'react-aria-components'
import { useNavigate } from 'react-router'
import { Button } from '@/components/actions/Button/Button.tsx'
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { EmptyState } from '@/components/feedback/EmptyState/EmptyState.tsx'
import { ErrorState } from '@/components/feedback/ErrorState/ErrorState.tsx'
import { SearchField } from '@/components/inputs/SearchField/SearchField.tsx'
import type { components } from '@/lib/api-types.ts'
import { pageNames } from '@/lib/copy.ts'
import { electivesPath, useElectivesAddress } from '@/lib/electivesAddress.ts'
import { actionLabels, explain } from '@/lib/errors.ts'
import { queries } from '@/lib/queryKeys.ts'
import { fits, keeping, matches, openingTab, putFirst } from './cards.ts'
import { CategoryTabs } from './components/CategoryTabs/CategoryTabs.tsx'
import { ElectiveCard } from './components/ElectiveCard/ElectiveCard.tsx'
import {
  noMatch,
  noMatchMessage,
  notCurrent,
  nothingFits,
  searchPlaceholder,
  showEveryCourse,
  showing,
} from './copy.ts'
import { useHearting } from './useHearting.ts'
import styles from './ElectivesPage.module.css'

type Elective = components['schemas']['Elective']
type Tab = components['schemas']['Tab']

export function ElectivesPage() {
  const address = useElectivesAddress()
  const { planId } = address
  const navigate = useNavigate()
  const electives = useQuery(queries.electives())
  // Her set names the plan the page is filtered to, and says whether it's one of her current plans
  const set = useQuery({ ...queries.plans(), enabled: planId !== null })
  const current = set.data?.plans.find((summary) => summary.id === planId)
  const fitting = planId !== null && electives.data ? keeping(electives.data.tabs, (card) => fits(card, planId)) : []
  // A plan outside her current set, or a current one nothing fits, is read for what to say about
  // it. With no plan in the address the read never goes out, so its id is never used.
  const plan = useQuery({
    ...queries.plan(planId ?? ''),
    enabled: planId !== null && set.data !== undefined && (current === undefined || fitting.length === 0),
  })
  const hearting = useHearting()
  const [search, setSearch] = useState('')
  // Her favourites as the page opened for this plan, which come first, and never move as she hearts.
  // Kept as the courses first arrive, which React draws again at once, before anything shows.
  const [opened, setOpened] = useState<{ planId: string | null; hearts: Set<string> } | null>(null)
  if (electives.data && opened?.planId !== planId) {
    const hearted = electives.data.tabs.flatMap((tab) => tab.courses.filter((card) => card.hearted))
    setOpened({ planId, hearts: new Set(hearted.map((card) => card.codes[0])) })
  }
  const favourite = (card: Elective) => opened?.hearts.has(card.codes[0]) ?? false

  const notHers = plan.error?.code === 'plan_not_found'
  const failed = electives.error ?? (planId === null ? null : set.error) ?? (notHers ? null : plan.error)
  // Every course, on the tab on screen
  const everyCourse = (tab: string | null) => <Link href={electivesPath({ planId: null, tab })}>{showEveryCourse}</Link>

  // The tabs with the cards matching the search, and the one on screen. Searching opens the first tab
  // with a match without changing the address, so clearing the search goes back to her tab.
  function shownOf(tabs: Tab[], first: (card: Elective) => boolean) {
    const shown = keeping(tabs, (card) => matches(card, search))
    return { shown, selected: openingTab(shown, address.tab, first) }
  }

  // Those tabs, with the cards that come first ahead of the rest
  function tabsOf({ shown, selected }: ReturnType<typeof shownOf>, first: (card: Elective) => boolean): ReactNode {
    if (selected === null) return <EmptyState title={noMatch} message={noMatchMessage(search)} />
    return (
      <CategoryTabs tabs={shown} selected={selected} onSelect={(tab) => void navigate(electivesPath({ ...address, tab }), { replace: true })}>
        {(tab) =>
          putFirst(tab.courses, first).map((card) => (
            <ElectiveCard key={card.codes[0]} card={card} onHeartChange={(heart) => hearting.mutate({ card, heart })} />
          ))
        }
      </CategoryTabs>
    )
  }

  const none = () => false
  let body: ReactNode = null
  if (failed) {
    const { title, message, reference } = explain(failed)
    body = (
      <ErrorState variant="region" tone="danger" icon="error" title={title} message={message} reference={reference}>
        <Button
          variant="secondary"
          onPress={() => {
            for (const read of [electives, set, plan]) if (read.isError) void read.refetch()
          }}
        >
          {actionLabels.retry}
        </Button>
      </ErrorState>
    )
  } else if (!electives.data) {
    body = null
  } else if (planId === null) {
    body = tabsOf(shownOf(electives.data.tabs, none), none)
  } else if (current && fitting.length > 0) {
    const count = fitting.reduce((total, tab) => total + tab.courses.length, 0)
    const view = shownOf(fitting, favourite)
    body = (
      <>
        <p className={styles.notice}>
          {showing(count, current.name)} {everyCourse(view.selected)}
        </p>
        {tabsOf(view, favourite)}
      </>
    )
  } else if (current && plan.data) {
    body = (
      <EmptyState
        title={nothingFits}
        message={plan.data.slots.map((slot) => slot.message).join(' ')}
        action={everyCourse(address.tab)}
      />
    )
  } else if (notHers && plan.error) {
    const { title, message } = explain(plan.error)
    body = (
      <>
        <ErrorState variant="inline" tone="warning" icon="warning" title={title} message={message} />
        {tabsOf(shownOf(electives.data.tabs, none), none)}
      </>
    )
  } else if (!current && plan.data) {
    body = (
      <>
        <p className={styles.notice}>{notCurrent}</p>
        {tabsOf(shownOf(electives.data.tabs, none), none)}
      </>
    )
  }

  return (
    <div className={styles.page}>
      <PageHeader title={pageNames.electives} />
      <SearchField label="Search Electives" placeholder={searchPlaceholder} value={search} onChange={setSearch} isDisabled={failed !== null} />
      {body}
    </div>
  )
}
