import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import themeScript from '../../public/theme.js?raw'
import { useAppearance } from './useAppearance.ts'

// What the browser does when a page loads: public/theme.js runs before anything paints
function loadPage() {
  delete document.documentElement.dataset.theme
  const script = document.createElement('script')
  script.textContent = themeScript
  document.head.append(script)
  script.remove()
  return document.documentElement.dataset.theme
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('appearance', () => {
  it('survives a reload', () => {
    const { result } = renderHook(() => useAppearance())
    act(() => result.current.choose('dark'))
    expect(loadPage()).toBe('dark')
  })

  it('falls back to Match System when storage is blocked', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    expect(loadPage()).toBe('system')

    // Choosing still works for the open page, even though nothing can be saved
    const { result } = renderHook(() => useAppearance())
    act(() => result.current.choose('light'))
    expect(document.documentElement.dataset.theme).toBe('light')
  })
})
