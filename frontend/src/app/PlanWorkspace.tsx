// The plan workspace at /plan and /plan/:planId, a stub until the shell branch builds its slots
import { PageHeader } from '@/components/content/PageHeader/PageHeader.tsx'
import { pageNames } from '@/lib/copy.ts'

export function PlanWorkspace() {
  return <PageHeader title={pageNames.plan} />
}
