// Applies the saved appearance before the first paint, so a student who chose Dark never sees a white
// flash. index.html loads it in <head>.
//   data-appearance on <html> is the choice: system, light or dark. src/lib/useAppearance.ts changes it
//   and saves it under the same key. Anything else, or blocked storage, means Match System.
//   data-theme is what is on screen, light or dark, and theme.css follows it. With Match System it
//   follows the system, live.
;(() => {
  const root = document.documentElement
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)')

  function applyTheme() {
    const choice = root.dataset.appearance
    if (choice === 'light' || choice === 'dark') root.dataset.theme = choice
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
  new MutationObserver(applyTheme).observe(root, { attributeFilter: ['data-appearance'] })
  systemDark.addEventListener('change', applyTheme)
})()
