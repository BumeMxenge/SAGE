// The page for an address that isn't one, a stub until the shell branch builds it
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { pageNames } from '@/lib/copy.ts'

export function NotFoundPage() {
  return <PageHeader title={pageNames.notFound} />
}
