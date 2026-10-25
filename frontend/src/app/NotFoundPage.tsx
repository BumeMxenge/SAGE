// The page for an address that isn't one, which holds only its heading (docs/shortfalls.md)
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { pageNames } from '@/lib/copy.ts'

export function NotFoundPage() {
  return <PageHeader title={pageNames.notFound} />
}
