// What Explore Electives shows, as the page's address says: ?plan=:planId keeps only the courses that
// fit one of her plans' complementary slots, and ?tab= picks the tab on screen. The address is the one
// record of these, so a reload, Back and a plan's slot card all land in the same place. Every screen
// that reads or writes them goes through here, as planAddress.ts does for a plan.
import { useSearchParams } from 'react-router'

// The tab is the address's word for it, which the page opens only if it shows that tab
type ElectivesAddress = { planId: string | null; tab: string | null }

export function readElectivesAddress(query: URLSearchParams): ElectivesAddress {
  return { planId: query.get('plan') || null, tab: query.get('tab') || null }
}

export function useElectivesAddress(): ElectivesAddress {
  const [query] = useSearchParams()
  return readElectivesAddress(query)
}

// The address that opens the page as asked. With no plan and no tab, it's the page itself.
export function electivesPath({ planId, tab }: ElectivesAddress): string {
  const query = new URLSearchParams()
  if (planId) query.set('plan', planId)
  if (tab) query.set('tab', tab)
  const search = query.toString()
  return search ? `/electives?${search}` : '/electives'
}
