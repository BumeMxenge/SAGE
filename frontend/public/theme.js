// Applies the saved appearance before the first paint, so a student who chose Dark never sees a white
// flash. index.html and design-system.html load it in <head>. src/lib/useAppearance.ts writes the
// same key. Anything but "light" or "dark", and blocked storage, means Match System.
;(() => {
  let choice = 'system'
  try {
    const saved = localStorage.getItem('sage-appearance')
    if (saved === 'light' || saved === 'dark') choice = saved
  } catch {
    // storage is blocked, as in some private windows
  }
  document.documentElement.dataset.theme = choice
})()
