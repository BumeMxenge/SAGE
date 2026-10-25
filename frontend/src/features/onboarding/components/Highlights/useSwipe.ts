// Turns one sideways gesture into one step: a swipe or a drag, by finger, pen or mouse, or a
// sideways trackpad scroll. A trackpad goes on sending wheel events after the fingers lift, its
// momentum, so after a step the stream is ignored for a rest, as the prototype's is: long enough
// for a gesture's momentum to die down, and short enough that the next gesture counts while the
// last one still coasts. It returns a ref for the element the gestures happen on.
import { useCallback } from 'react'

// How far a swipe or a drag travels sideways before it counts, in CSS pixels
const travel = 60
// How far a trackpad's scroll travels sideways before it counts, in CSS pixels, and how long a pause in
// it starts it afresh, in milliseconds
const scrollTravel = 110
const pause = 170
// How long the stream is ignored after a step, in milliseconds: the prototype's 620 ms slide and 140 ms
// more. Reduced motion keeps it, though the slide is instant, as it is there for the momentum.
const rest = 760

export function useSwipe(step: (by: 1 | -1) => void) {
  return useCallback(
    (element: HTMLElement | null) => {
      if (!element) return
      let scrolled = 0
      let resting = false
      let paused: ReturnType<typeof setTimeout> | undefined
      let rested: ReturnType<typeof setTimeout> | undefined
      let start: number | null = null

      function onWheel(event: WheelEvent) {
        // Mostly up or down is a scroll of the page
        if (Math.abs(event.deltaX) <= Math.abs(event.deltaY)) return
        // Stops the browser going back a page on a sideways swipe, which a passive listener can't
        event.preventDefault()
        if (resting) return
        clearTimeout(paused)
        paused = setTimeout(() => {
          scrolled = 0
        }, pause)
        // A turn the other way starts afresh
        if (Math.sign(event.deltaX) !== Math.sign(scrolled)) scrolled = 0
        scrolled += event.deltaX
        if (Math.abs(scrolled) < scrollTravel) return
        step(scrolled > 0 ? 1 : -1)
        scrolled = 0
        resting = true
        rested = setTimeout(() => {
          resting = false
        }, rest)
      }

      function onPointerDown(event: PointerEvent) {
        start = event.clientX
      }

      // A drag or swipe to the left shows the next highlight, as turning a page does. It has no
      // momentum, so it needs no rest.
      function onPointerUp(event: PointerEvent) {
        if (start === null) return
        const dragged = event.clientX - start
        start = null
        if (Math.abs(dragged) >= travel) step(dragged < 0 ? 1 : -1)
      }

      element.addEventListener('wheel', onWheel, { passive: false })
      element.addEventListener('pointerdown', onPointerDown)
      element.addEventListener('pointerup', onPointerUp)
      return () => {
        element.removeEventListener('wheel', onWheel)
        element.removeEventListener('pointerdown', onPointerDown)
        element.removeEventListener('pointerup', onPointerUp)
        clearTimeout(paused)
        clearTimeout(rested)
      }
    },
    [step],
  )
}
