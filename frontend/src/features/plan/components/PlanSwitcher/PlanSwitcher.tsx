// A choice of her plans: those her answers kept, by position, then those they hid, under their own
// title, as any of them can still open. Each shows its name, wrapping when it's long, its electives'
// codes under it as the API joins them, and its credits. A plan with no electives has no codes line.
// The plan switcher atop the plan is outlined. Compare with Another Plan, in the second compare panel,
// is quiet, as the panel's title names its plan.
import { Select } from '@/components/inputs/Select/Select.tsx'
import { SelectItem } from '@/components/inputs/Select/SelectItem.tsx'
import { SelectSection } from '@/components/inputs/Select/SelectSection.tsx'
import type { components } from '@/lib/api-types.ts'

type PlanSummary = components['schemas']['PlanSummary']

type PlanSwitcherProps = {
  label: string
  variant: 'outlined' | 'quiet'
  plans: PlanSummary[]
  selected: string
  onChange: (planId: string) => void
}

export function PlanSwitcher({ label, variant, plans, selected, onChange }: PlanSwitcherProps) {
  const sorted = [...plans].sort((a, b) => a.position - b.position)
  const hidden = sorted.filter((plan) => plan.hidden)
  const item = (plan: PlanSummary) => (
    <SelectItem key={plan.id} id={plan.id} description={plan.combination ?? undefined} detail={`${plan.credits} credits`}>
      {plan.name}
    </SelectItem>
  )
  return (
    <Select
      label={label}
      variant={variant}
      selectedKey={selected}
      onSelectionChange={(key) => {
        if (key !== null) onChange(String(key))
      }}
    >
      {sorted.filter((plan) => !plan.hidden).map(item)}
      {hidden.length > 0 && <SelectSection title="Hidden by Your Answers">{hidden.map(item)}</SelectSection>}
    </Select>
  )
}
