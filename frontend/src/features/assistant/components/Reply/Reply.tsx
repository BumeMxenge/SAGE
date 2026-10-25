// One reply from SAGE: its words, with the line breaks it wrote, then the handbook quotes it rests on,
// numbered in the order the API sends them, each over where it is in the handbook. A line hands the
// question to her student advisor when the reply does, and a link opens a plan it offers, hidden plans
// included, alone and at the term on screen. A link to the plan already open alone would go nowhere,
// so it's left out.
import { useId } from 'react'
import { Link } from 'react-aria-components'
import type { components } from '@/lib/api-types.ts'
import { type PlanAddress, planPath } from '@/lib/planAddress.ts'
import styles from './Reply.module.css'

type Message = components['schemas']['Message']
type PlanSummary = components['schemas']['PlanSummary']

type ReplyProps = { reply: Message; plans: PlanSummary[]; address: PlanAddress }

export function Reply({ reply, plans, address }: ReplyProps) {
  const sourcesId = useId()
  const offered = reply.open_plan_id
  const openAlone = address.compareWith === null && offered === address.planId
  const name = plans.find((plan) => plan.id === offered)?.name
  return (
    <div className={styles.reply}>
      <p className={styles.content}>
        <span className="visually-hidden">SAGE replied: </span>
        {reply.content}
      </p>
      {reply.citations.length > 0 && (
        <div>
          <p id={sourcesId} className={styles.sourcesTitle}>
            Sources
          </p>
          <ol aria-labelledby={sourcesId} className={styles.sources}>
            {reply.citations.map((citation) => (
              <li key={citation.position}>
                <q>{citation.quote}</q>
                <span className={styles.where}>
                  {citation.source}, {citation.section}, page {citation.page}
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}
      {reply.referral && <p className={styles.referral}>Your student advisor can help with this.</p>}
      {offered !== null && !openAlone && (
        <Link href={planPath({ planId: offered, compareWith: null, term: address.term, preview: null })} className={styles.openPlan}>
          Open {name ?? 'Plan'}
        </Link>
      )}
    </div>
  )
}
