// Reads tokens.css and theme.css and checks WCAG 2.2 AA in both themes: 4.5:1 for text, and 3:1 for
// the focus ring, the control border and, in light, the field border. In dark, fields have no border
// and are identified by their placeholder, icon or label (approved difference 2). Decorative borders
// and disabled text are left out, as WCAG allows.
import { describe, expect, it } from 'vitest'
import themeCss from './theme.css?raw'
import tokensCss from './tokens.css?raw'

type Theme = 'light' | 'dark'

// WCAG contrast ratio between two hex colours, from 1 (the same) to 21 (black on white)
function contrast(foreground: string, background: string): number {
  const luminance = (hex: string) => {
    const digits = hex.replace('#', '')
    const full = digits.length === 3 ? digits.split('').map((digit) => digit + digit).join('') : digits
    const [red, green, blue] = [0, 2, 4].map((start) => {
      const scaled = parseInt(full.slice(start, start + 2), 16) / 255
      return scaled <= 0.04045 ? scaled / 12.92 : ((scaled + 0.055) / 1.055) ** 2.4
    })
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue
  }
  const [lighter, darker] = [luminance(foreground), luminance(background)].sort((a, b) => b - a)
  return (lighter + 0.05) / (darker + 0.05)
}

function declarations(css: string): Map<string, string> {
  const tokens = new Map<string, string>()
  for (const [, name, value] of css.replace(/\/\*[\s\S]*?\*\//g, '').matchAll(/(--[\w-]+):\s*([^;]+);/g)) {
    tokens.set(name, value.trim())
  }
  return tokens
}

// Every token's value in each theme: the shared tokens, plus that theme's block of theme.css
const darkStart = themeCss.indexOf(":root[data-theme='dark']")
const shared = declarations(tokensCss)
const tokens: Record<Theme, Map<string, string>> = {
  light: new Map([...shared, ...declarations(themeCss.slice(0, darkStart))]),
  dark: new Map([...shared, ...declarations(themeCss.slice(darkStart))]),
}

function value(name: string, theme: Theme): string {
  const found = tokens[theme].get(name)
  if (found === undefined) throw new Error(`${name} is not a token`)
  return found
}

const surfaces = ['--color-surface', '--color-surface-raised', '--color-surface-muted', '--color-surface-field']
const courseColours = [...tokens.light.keys()].filter((name) => name.startsWith('--color-course-'))

// Placeholders use --color-text-secondary, so its check on --color-surface-field is the one a dark
// field relies on to be identified
const checks: { token: string; against: string[]; minimum: number; theme?: Theme }[] = [
  ...[
    '--color-text',
    '--color-text-secondary',
    '--color-text-accent',
    '--color-text-danger',
    '--color-text-warning',
    '--color-link',
    '--color-link-hover',
  ].map((token) => ({ token, against: surfaces, minimum: 4.5 })),
  { token: '--color-text-danger', against: ['--color-danger-tint'], minimum: 4.5 },
  { token: '--color-text-warning', against: ['--color-warning-tint'], minimum: 4.5 },
  { token: '--color-on-primary', against: ['--color-primary', '--color-surface-inverse'], minimum: 4.5 },
  { token: '--color-on-fill', against: ['--color-sign-in', '--color-accent-fill', ...courseColours], minimum: 4.5 },
  { token: '--color-border-field', against: surfaces, minimum: 3, theme: 'light' },
  { token: '--color-border-control', against: surfaces, minimum: 3 },
  { token: '--color-focus', against: surfaces, minimum: 3 },
]

describe.each(['light', 'dark'] as const)('%s theme', (theme) => {
  const inTheme = checks.filter((check) => check.theme === undefined || check.theme === theme)
  it.each(inTheme.map((check) => [check.token, check] as const))('%s meets its contrast', (_, check) => {
    for (const against of check.against) {
      expect(contrast(value(check.token, theme), value(against, theme)), `${check.token} on ${against}`).toBeGreaterThanOrEqual(
        check.minimum,
      )
    }
  })
})

// A colour added to the light block only would stay light in the dark theme
it('defines the same tokens in both themes', () => {
  expect([...tokens.dark.keys()].sort()).toEqual([...tokens.light.keys()].sort())
})

it('checks all eight course colours', () => {
  const white = checks.find((check) => check.token === '--color-on-fill')
  expect(courseColours).toHaveLength(8)
  expect(white?.against).toHaveLength(10) // the sign-in button, the accent fill and the eight course colours
})

// The audit's published ratios (SAGE_M3_DESIGN_AUDIT.md section 2), so a broken formula can't pass
it('matches the ratios the audit measured', () => {
  expect(contrast('#636a6e', '#ececee')).toBeCloseTo(4.66, 2)
  expect(contrast('#8f979a', '#2a2b2e')).toBeCloseTo(4.76, 2)
  expect(contrast('#000000', '#ffffff')).toBeCloseTo(21, 5)
})
