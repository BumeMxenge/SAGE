// Reads tokens.css and theme.css as text, for the contrast test and the review page, so both report
// the same numbers.
import { contrast } from '@/lib/contrast.ts'

export type Theme = 'light' | 'dark'

// Every token's value in each theme: the shared tokens, plus that theme's block of theme.css
export type Tokens = Record<Theme, Map<string, string>>

function declarations(css: string): Map<string, string> {
  const tokens = new Map<string, string>()
  for (const [, name, value] of css.replace(/\/\*[\s\S]*?\*\//g, '').matchAll(/(--[\w-]+):\s*([^;]+);/g)) {
    tokens.set(name, value.trim().replace(/\s+/g, ' '))
  }
  return tokens
}

export function parseTokens(sharedCss: string, themeCss: string): Tokens {
  const darkStart = themeCss.indexOf(":root[data-theme='dark']")
  if (darkStart === -1) throw new Error('theme.css has no dark block')
  const shared = declarations(sharedCss)
  return {
    light: new Map([...shared, ...declarations(themeCss.slice(0, darkStart))]),
    dark: new Map([...shared, ...declarations(themeCss.slice(darkStart))]),
  }
}

export function tokensWithPrefix(tokens: Tokens, prefix: string): [string, string][] {
  return [...tokens.light].filter(([name]) => name.startsWith(prefix))
}

export function tokenValue(tokens: Tokens, name: string, theme: Theme): string {
  const value = tokens[theme].get(name)
  if (value === undefined) throw new Error(`${name} is not a token`)
  return value
}

// A check with a theme applies to that theme only
export type ContrastCheck = { token: string; against: string[]; minimum: number; theme?: Theme }

export const surfaces = ['--color-surface', '--color-surface-raised', '--color-surface-muted', '--color-surface-field']

// WCAG 2.2 AA: 4.5:1 for text, 3:1 for the focus ring and, in light, the field outline. In dark,
// fields have no outline, only their shaded fill. Decorative borders and disabled text are left out,
// as WCAG allows.
export function contrastChecks(tokens: Tokens): ContrastCheck[] {
  const courseColours = [...tokens.light.keys()].filter((name) => name.startsWith('--color-course-'))
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
    { token: '--color-on-fill', against: ['--color-sign-in', '--color-accent-fill', ...courseColours], minimum: 4.5 },
    { token: '--color-border-input', against: surfaces, minimum: 3, theme: 'light' },
    { token: '--color-focus', against: surfaces, minimum: 3 },
  ]
}

export function checksFor(tokens: Tokens, theme: Theme): ContrastCheck[] {
  return contrastChecks(tokens).filter((check) => check.theme === undefined || check.theme === theme)
}

export function ratio(tokens: Tokens, token: string, against: string, theme: Theme): number {
  return contrast(tokenValue(tokens, token, theme), tokenValue(tokens, against, theme))
}
