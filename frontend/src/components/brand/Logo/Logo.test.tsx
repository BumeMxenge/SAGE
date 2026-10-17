import { cleanup, render } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { Logo } from './Logo.tsx'

afterEach(cleanup)

it('gives every logo on a page its own title id, each named by its own title', () => {
  const { container } = render(
    <>
      <Logo variant="full" />
      <Logo variant="compact" />
      <Logo variant="mark" />
    </>,
  )
  const titles = [...container.querySelectorAll('title')]
  expect(titles).toHaveLength(6) // three logos, each with a light and a dark file
  expect(new Set(titles.map((title) => title.id)).size).toBe(6)
  for (const title of titles) {
    expect(title.id).not.toBe('')
    expect(title.closest('svg')?.getAttribute('aria-labelledby')).toBe(title.id)
  }
  expect(titles.map((title) => title.textContent)).toContain('SAGE, Student Advisor for Guided Enrolment')
})

it('hides Microsoft’s mark from screen readers, since the button names itself', () => {
  const { container } = render(<Logo variant="microsoft" />)
  expect(container.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true')
})
