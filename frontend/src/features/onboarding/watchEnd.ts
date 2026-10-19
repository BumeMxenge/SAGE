// Calls onEnd once a scrolling box has been scrolled to its end, or at once when it has nothing to
// scroll, as the prototype's review lets a year be confirmed only once its list has been seen to the
// end. Within 6 px of the end counts, as in the prototype. It also watches the box's size and its
// content's, so a box that a taller window, or a removed course, leaves with nothing to scroll counts
// too. It returns the clean-up, for a callback ref.
export function watchEnd(box: HTMLElement, onEnd: () => void): () => void {
  function check() {
    if (box.scrollTop + box.clientHeight >= box.scrollHeight - 6) onEnd()
  }
  check()
  box.addEventListener('scroll', check, { passive: true })
  const sizes = new ResizeObserver(check)
  sizes.observe(box)
  if (box.firstElementChild) sizes.observe(box.firstElementChild)
  return () => {
    box.removeEventListener('scroll', check)
    sizes.disconnect()
  }
}
