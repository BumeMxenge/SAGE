// The appearance setting for a menu: Match System, Light or Dark. The choice is data-theme on <html>,
// kept in localStorage so public/theme.js can restore it before the next page paints.
import { useState } from 'react'

export type Appearance = 'system' | 'light' | 'dark'

function current(): Appearance {
  const theme = document.documentElement.dataset.theme
  return theme === 'light' || theme === 'dark' ? theme : 'system'
}

export function useAppearance() {
  const [appearance, setAppearance] = useState(current)

  function choose(next: Appearance) {
    document.documentElement.dataset.theme = next
    try {
      localStorage.setItem('sage-appearance', next)
    } catch {
      // storage is blocked, so the choice lasts until the page closes
    }
    setAppearance(next)
  }

  return { appearance, choose }
}
