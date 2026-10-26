// A student's page as the first load draws it in her frame while the guard decides: the page itself,
// held, so it shows its skeleton and reads nothing. It comes from the same file the route loads, so
// the first download carries nothing more, and until that file arrives the frame shows alone.
import { type ComponentType, type LazyExoticComponent, Suspense } from 'react'

type HeldPageProps = { page: LazyExoticComponent<ComponentType<{ held?: boolean }>> }

export function HeldPage({ page: Page }: HeldPageProps) {
  return (
    <Suspense fallback={null}>
      <Page held />
    </Suspense>
  )
}
