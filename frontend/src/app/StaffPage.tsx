// The page staff see, which holds only its heading (docs/shortfalls.md)
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { pageNames } from '@/lib/copy.ts'

export function StaffPage() {
  return <PageHeader title={pageNames.staff} />
}
