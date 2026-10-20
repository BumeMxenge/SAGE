// The trackpad's rest after a step, timed as the prototype's: its 620 ms slide and 140 ms more. A swipe
// inside the rest is ignored with the momentum, and one after it moves on, though the stream of wheel
// events never paused in between, as it doesn't while the last swipe still coasts.
import { renderHook } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { useSwipe } from './useSwipe.ts'

afterEach(() => {
  vi.useRealTimers()
})

it('ignores a swipe inside the rest after a step, and takes one after it while the last still coasts', () => {
  vi.useFakeTimers()
  // Milliseconds since the first swipe, and each step with the moment it came
  let now = 0
  const steps: string[] = []
  const area = document.createElement('div')
  renderHook(() =>
    useSwipe((by) => {
      steps.push(`${by > 0 ? 'on' : 'back'} at ${now} ms`)
    }),
  ).result.current(area)
  const scroll = (deltaX: number) => area.dispatchEvent(new WheelEvent('wheel', { deltaX, cancelable: true }))
  // Three 40 px events pass the 110 px a step needs
  const swipe = () => {
    for (const deltaX of [40, 40, 40]) scroll(deltaX)
  }
  swipe()
  // Momentum trickles in every 50 ms, never pausing, and swipes come at 700 ms, inside the 760 ms
  // rest, and at 800 ms, after it
  for (now = 50; now <= 800; now += 50) {
    vi.advanceTimersByTime(50)
    if (now === 700 || now === 800) swipe()
    else scroll(2)
  }
  expect(steps).toEqual(['on at 0 ms', 'on at 800 ms'])
})
