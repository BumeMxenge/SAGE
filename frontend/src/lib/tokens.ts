// Reads tokens.css as text, for the contrast test and the review page, so both report the same numbers.
import { contrast } from '@/lib/contrast.ts'

export type Theme = 'light' | 'dark'

// Every custom property in the stylesheet, by name. A name set twice keeps its first value.
export function parseTokens(css: string): Map<string, string> {
  const tokens = new Map<string, string>()
  for (const [, name, value] of css.replace(/\/\*[\s\S]*?\*\//g, '').matchAll(/(--[\w-]+):\s*([^;]+);/g)) {
    if (!tokens.has(name)) tokens.set(name, value.trim().replace(/\s+/g, ' '))
  }
  return tokens
}

export function tokensWithPrefix(tokens: Map<string, string>, prefix: string): [string, string][] {
  return [...tokens].filter(([name]) => name.startsWith(prefix))
}

// A colour token's value in one theme. light-dark(a, b) is split at its top-level comma.
export function colourValue(tokens: Map<string, string>, name: string, theme: Theme): string {
  const value = tokens.get(name)
  if (value === undefined) throw new Error(`${name} is not a token in tokens.css`)
  const inner = /^light-dark\((.*)\)$/.exec(value)?.[1]
  if (inner === undefined) return value
  let depth = 0
  for (const [index, character] of inner.split('').entries()) {
    if (character === '(') depth++
    if (character === ')') depth--
    if (character === ',' && depth === 0) {
      return (theme === 'light' ? inner.slice(0, index) : inner.slice(index + 1)).trim()
    }
  }
  throw new Error(`${name} has no comma inside light-dark()`)
}

export type ContrastCheck = { token: string; against: string[]; minimum: number }

export const surfaces = ['--color-surface', '--color-surface-raised', '--color-surface-muted', '--color-surface-field']

// WCAG 2.2 AA: 4.5:1 for text, 3:1 for the input border and the focus ring. Decorative borders and
// disabled text are left out, as WCAG allows.
export function contrastChecks(tokens: Map<string, string>): ContrastCheck[] {
  const courseColours = [...tokens.keys()].filter((name) => name.startsWith('--color-course-'))
  const text = [
    '--color-text',
    '--color-text-secondary',
    '--color-text-accent',
    '--color-text-danger',
    '--color-text-warning',
    '--color-link',
    '--color-link-hover',
  ]
  return [
    ...text.map((token) => ({ token, against: surfaces, minimum: 4.5 })),
    { token: '--color-text-danger', against: ['--color-danger-tint'], minimum: 4.5 },
    { token: '--color-on-primary', against: ['--color-primary', '--color-surface-inverse'], minimum: 4.5 },
    { token: '--color-on-fill', against: ['--color-accent-fill', ...courseColours], minimum: 4.5 },
    { token: '--color-border-input', against: surfaces, minimum: 3 },
    { token: '--color-focus', against: surfaces, minimum: 3 },
  ]
}

export function ratio(tokens: Map<string, string>, token: string, against: string, theme: Theme): number {
  return contrast(colourValue(tokens, token, theme), colourValue(tokens, against, theme))
}
