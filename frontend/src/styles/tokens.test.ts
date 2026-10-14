// Reads tokens.css and theme.css and checks WCAG 2.2 AA in both themes (the checks are in
// lib/tokens.ts, which the review page shows too). Decorative borders and disabled text are left out,
// as WCAG allows.
import { describe, expect, it } from 'vitest'
import { contrast } from '@/lib/contrast.ts'
import { contrastChecks, parseTokens, ratio, tokensWithPrefix } from '@/lib/tokens.ts'
import themeCss from './theme.css?raw'
import tokensCss from './tokens.css?raw'

const tokens = parseTokens(tokensCss, themeCss)
const checks = contrastChecks(tokens)

describe.each(['light', 'dark'] as const)('%s theme', (theme) => {
  it.each(checks.map((check) => [check.token, check] as const))('%s meets its contrast', (_, check) => {
    for (const against of check.against) {
      expect(ratio(tokens, check.token, against, theme), `${check.token} on ${against}`).toBeGreaterThanOrEqual(check.minimum)
    }
  })
})

// A colour added to the light block only would stay light in the dark theme
it('defines the same tokens in both themes', () => {
  expect([...tokens.dark.keys()].sort()).toEqual([...tokens.light.keys()].sort())
})

it('checks all eight course colours', () => {
  const white = checks.find((check) => check.token === '--color-on-fill')
  expect(tokensWithPrefix(tokens, '--color-course-')).toHaveLength(8)
  expect(white?.against).toHaveLength(10) // the sign-in button, the accent fill and the eight course colours
})

// The audit's published ratios (SAGE_M3_DESIGN_AUDIT.md section 2), so a broken formula can't pass
it('matches the ratios the audit measured', () => {
  expect(contrast('#636a6e', '#ececee')).toBeCloseTo(4.66, 2)
  expect(contrast('#8f979a', '#2a2b2e')).toBeCloseTo(4.76, 2)
  expect(contrast('#000000', '#ffffff')).toBeCloseTo(21, 5)
})
