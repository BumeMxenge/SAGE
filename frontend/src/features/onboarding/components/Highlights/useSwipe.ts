// Turns one sideways gesture into one step: a swipe or a drag, by finger, pen or mouse, or a sideways
// trackpad scroll. A trackpad sends a stream of wheel events, its momentum included, so after a step
// the stream must pause before the next gesture can begin: one gesture never moves two highlights.
// It returns a ref for the element the gestures happen on.
import { useCallback } from 'react'

// How far a gesture travels sideways before it counts, in CSS pixels
const travel = 60
// How long a trackpad's stream must pause to end its gesture, in milliseconds
const pause = 200

export function useSwipe(step: (by: 1 | -1) => void) {
  return useCallback(
    (element: HTMLElement | null) => {
      if (!element) return
      let scrolled = 0
      let stepped = false
      let timer: ReturnType<typeof setTimeout> | undefined
      let start: number | null = null

      function onWheel(event: WheelEvent) {
        // Mostly up or down is a scroll of the page
        if (Math.abs(event.deltaX) <= Math.abs(event.deltaY)) return
        // Stops the browser going back a page on a sideways swipe, which a passive listener can't
        event.preventDefault()
        clearTimeout(timer)
        timer = setTimeout(() => {
          scrolled = 0
          stepped = false
        }, pause)
        if (stepped) return
        scrolled += event.deltaX
        if (Math.abs(scrolled) < travel) return
        stepped = true
        step(scrolled > 0 ? 1 : -1)
      }

      function onPointerDown(event: PointerEvent) {
        start = event.clientX
      }

      // A drag or swipe to the left shows the next highlight, as turning a page does
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
        clearTimeout(timer)
      }
    },
    [step],
  )
}
