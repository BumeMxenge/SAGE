import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { Button } from './Button.tsx'

afterEach(cleanup)

it('keeps the label an icon-only button is given', () => {
  render(
    <Button icon="add" iconOnly aria-label="Add a course to 2024">
      Add a Course
    </Button>,
  )
  expect(screen.getByRole('button', { name: 'Add a course to 2024' })).toBeTruthy()
})
