// Applies the saved appearance before the first paint, so a student who chose Dark never sees a white
// flash. index.html loads it in <head>.
//   data-appearance on <html> is the choice: system, light or dark. src/lib/useAppearance.ts changes it
//   and saves it under the same key. Anything else, or blocked storage, means Match System.
//   data-theme is what is on screen, light or dark, and theme.css follows it. With Match System it
//   follows the system, live.
//   Onboarding is designed in light only. Its pages keep data-light-only on <html> while they are open
//   (src/features/onboarding/useLightOnly.ts), which shows light whatever the choice. Their addresses
//   paint light from the first frame, before the app has run; once the app draws its first page, that
//   page decides, so a student sent on from one of them to their plans gets their own choice.
;(() => {
  const root = document.documentElement
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)')
  let opening = ['/sign-in', '/onboarding', '/wrong-account'].includes(window.location.pathname)

  function applyTheme() {
    const choice = root.dataset.appearance
    if (opening || root.hasAttribute('data-light-only')) root.dataset.theme = 'light'
    else if (choice === 'light' || choice === 'dark') root.dataset.theme = choice
    else root.dataset.theme = systemDark.matches ? 'dark' : 'light'
  }

  let saved = null
  try {
    saved = localStorage.getItem('sage-appearance')
  } catch {
    // storage is blocked, as in some private windows
  }
  root.dataset.appearance = saved === 'light' || saved === 'dark' ? saved : 'system'
  applyTheme()
  new MutationObserver(applyTheme).observe(root, { attributeFilter: ['data-appearance', 'data-light-only'] })
  systemDark.addEventListener('change', applyTheme)

  if (opening) {
    document.addEventListener('DOMContentLoaded', () => {
      const firstPage = new MutationObserver(() => {
        firstPage.disconnect()
        opening = false
        applyTheme()
      })
      firstPage.observe(document.getElementById('root'), { childList: true })
    })
  }
})()
