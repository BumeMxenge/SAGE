import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import themeScript from '../../public/theme.js?raw'
import { useAppearance } from './useAppearance.ts'

// The system's own setting, which jsdom doesn't have. The page's script reads it from window.
function systemIsDark(dark: boolean) {
  window.matchMedia = () => ({ matches: dark, addEventListener: () => undefined }) as unknown as MediaQueryList
}

// What the browser does when a page loads: public/theme.js runs before anything paints
function loadPage() {
  const root = document.documentElement
  delete root.dataset.appearance
  delete root.dataset.theme
  const script = document.createElement('script')
  script.textContent = themeScript
  document.head.append(script)
  script.remove()
  return { appearance: root.dataset.appearance, theme: root.dataset.theme }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('appearance', () => {
  it('survives a reload', () => {
    systemIsDark(false)
    loadPage()
    const { result } = renderHook(() => useAppearance())
    act(() => result.current.choose('dark'))
    expect(loadPage()).toEqual({ appearance: 'dark', theme: 'dark' })
  })

  it('falls back to Match System, following the system, when storage is blocked', async () => {
    systemIsDark(true)
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    expect(loadPage()).toEqual({ appearance: 'system', theme: 'dark' })

    // Choosing still works for the open page, even though nothing can be saved
    const { result } = renderHook(() => useAppearance())
    act(() => result.current.choose('light'))
    await waitFor(() => expect(document.documentElement.dataset.theme).toBe('light'))
  })
})
