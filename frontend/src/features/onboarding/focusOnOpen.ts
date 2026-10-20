// The ref for a step, or a year of the review, as it opens: focus moves to it, so a screen reader starts
// reading there, and the page shows it from the top. It is one function for the module's life, so
// React calls it only when its element mounts, never again on a later render.
export function focusOnOpen(element: HTMLElement | null): void {
  if (!element) return
  element.focus({ preventScroll: true })
  scrollTo(0, 0)
}
