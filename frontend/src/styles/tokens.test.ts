// Reads tokens.css and checks WCAG 2.2 AA in both themes: 4.5:1 for text, 3:1 for the input border and
// the focus ring. Decorative borders and disabled text are left out, as WCAG allows.
import { describe, expect, it } from 'vitest'
import { contrast } from '@/lib/contrast.ts'
import tokensCss from './tokens.css?raw'

type Pair = { light: string; dark: string }

// Every hex colour token, as its light and dark value
const tokens = new Map<string, Pair>()
for (const [, name, value] of tokensCss.matchAll(/^\s*(--color-[\w-]+):\s*(.+?);/gm)) {
  const lightDark = /^light-dark\((#\w+),\s*(#\w+)\)$/.exec(value)
  if (lightDark) tokens.set(name, { light: lightDark[1], dark: lightDark[2] })
  else if (/^#\w+$/.test(value)) tokens.set(name, { light: value, dark: value })
}

function colour(name: string, theme: keyof Pair): string {
  const pair = tokens.get(name)
  if (!pair) throw new Error(`${name} is not a hex colour token in tokens.css`)
  return pair[theme]
}

const surfaces = ['--color-surface', '--color-surface-raised', '--color-surface-muted', '--color-surface-field']
const textTokens = [
  '--color-text',
  '--color-text-secondary',
  '--color-text-accent',
  '--color-text-danger',
  '--color-text-warning',
  '--color-link',
  '--color-link-hover',
]
const courseColours = [...tokens.keys()].filter((name) => name.startsWith('--color-course-'))

describe.each(['light', 'dark'] as const)('%s theme', (theme) => {
  it.each(textTokens)('%s reaches 4.5:1 on every surface', (token) => {
    for (const surface of surfaces) {
      expect(contrast(colour(token, theme), colour(surface, theme)), `${token} on ${surface}`).toBeGreaterThanOrEqual(4.5)
    }
  })

  it('danger text reaches 4.5:1 on the error tile', () => {
    expect(contrast(colour('--color-text-danger', theme), colour('--color-danger-tint', theme))).toBeGreaterThanOrEqual(4.5)
  })

  it('button and tooltip text reaches 4.5:1 on its fill', () => {
    const onPrimary = colour('--color-on-primary', theme)
    expect(contrast(onPrimary, colour('--color-primary', theme))).toBeGreaterThanOrEqual(4.5)
    expect(contrast(onPrimary, colour('--color-surface-inverse', theme))).toBeGreaterThanOrEqual(4.5)
  })

  it('white text reaches 4.5:1 on the accent fill and every course colour', () => {
    expect(courseColours).toHaveLength(8)
    for (const fill of ['--color-accent-fill', ...courseColours]) {
      expect(contrast(colour('--color-on-fill', theme), colour(fill, theme)), fill).toBeGreaterThanOrEqual(4.5)
    }
  })

  it.each(['--color-border-input', '--color-focus'])('%s reaches 3:1 on every surface', (token) => {
    for (const surface of surfaces) {
      expect(contrast(colour(token, theme), colour(surface, theme)), `${token} on ${surface}`).toBeGreaterThanOrEqual(3)
    }
  })
})

// The audit's published ratios (SAGE_M3_DESIGN_AUDIT.md section 2), so a broken formula can't pass
it('matches the ratios the audit measured', () => {
  expect(contrast('#636a6e', '#ececee')).toBeCloseTo(4.66, 2)
  expect(contrast('#8f979a', '#2a2b2e')).toBeCloseTo(4.76, 2)
  expect(contrast('#000000', '#ffffff')).toBeCloseTo(21, 5)
})
