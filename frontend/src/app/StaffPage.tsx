// The page staff see, a stub until the shell branch builds it
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { pageNames } from '@/lib/copy.ts'

export function StaffPage() {
  return <PageHeader title={pageNames.staff} />
}
