// Content that stands in a skeleton's place until its read lands. While the read is on its way the
// skeleton shows, with a status line saying what is loading, as screen readers skip the skeleton. The
// content then takes its place and fades in, once, over the fast motion token, which reduced motion
// makes 0. Content that was there from the start, as from the cache, shows at once, and so does
// whatever changes inside it later. Once its content has shown, it never goes back to the skeleton:
// reads are kept until Sign Out, which empties them on the way out. A read that failed shows nothing,
// until the app's error states come. It adds no box of its own, so the content lays out as if it
// weren't there.
import { type ReactNode, useState } from 'react'
import styles from './Arrival.module.css'

type ArrivalProps<T> = {
  // What the content is drawn from, once its read has landed
  data: T | undefined
  // Whether that read is still on its way
  waiting: boolean
  skeleton: ReactNode
  // What a screen reader hears while the skeleton shows, such as "Loading your plan…". Where several
  // wait on one read, one says it.
  status?: string
  children: (data: T) => ReactNode
}

// Nothing shown yet, the skeleton showing, the content fading in in its place, or the content at rest
type Phase = 'empty' | 'waiting' | 'arriving' | 'shown'

export function Arrival<T>({ data, waiting, skeleton, status, children }: ArrivalProps<T>) {
  const [phase, setPhase] = useState<Phase>(data === undefined ? 'empty' : 'shown')
  const fresh = phase === 'empty' || phase === 'waiting'
  if (data === undefined) {
    if (!fresh || !waiting) return null
    if (phase === 'empty') setPhase('waiting')
    return (
      <>
        {skeleton}
        {status && <output className="visually-hidden">{status}</output>}
      </>
    )
  }
  if (fresh) setPhase(phase === 'waiting' ? 'arriving' : 'shown')
  return (
    <span className={phase === 'arriving' ? styles.arriving : styles.shown} onAnimationEnd={() => setPhase('shown')}>
      {children(data)}
    </span>
  )
}
