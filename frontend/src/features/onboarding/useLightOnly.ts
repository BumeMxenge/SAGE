// Onboarding is designed in light only, so its pages show light whatever the system or the student's
// appearance choice says. While a page that calls this is open, <html> carries data-light-only, which
// public/theme.js turns into the light theme, for its dialogs and popovers too. Leaving takes it off,
// in the same commit that draws the next page, and theme.js puts the student's own choice back.
import { useLayoutEffect } from 'react'

export function useLightOnly(): void {
  useLayoutEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-light-only', '')
    return () => root.removeAttribute('data-light-only')
  }, [])
}
