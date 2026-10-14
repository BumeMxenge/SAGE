// The appearance setting for a menu: Match System, Light or Dark. The choice is data-appearance on
// <html>, kept in localStorage. public/theme.js turns it into data-theme, the theme on screen, and
// restores it before the next page paints.
import { useState } from 'react'

export type Appearance = 'system' | 'light' | 'dark'

function current(): Appearance {
  const choice = document.documentElement.dataset.appearance
  return choice === 'light' || choice === 'dark' ? choice : 'system'
}

export function useAppearance() {
  const [appearance, setAppearance] = useState(current)

  function choose(next: Appearance) {
    document.documentElement.dataset.appearance = next
    try {
      localStorage.setItem('sage-appearance', next)
    } catch {
      // storage is blocked, so the choice lasts until the page closes
    }
    setAppearance(next)
  }

  return { appearance, choose }
}
