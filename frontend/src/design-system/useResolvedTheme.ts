// The theme actually on screen: Light or Dark, with Match System resolved to the system's choice.
import type { Appearance } from '@/lib/useAppearance.ts'
import type { Theme } from '@/lib/tokens.ts'
import { useMediaQuery } from '@/design-system/useMediaQuery.ts'

export function useResolvedTheme(appearance: Appearance): Theme {
  const systemDark = useMediaQuery('(prefers-color-scheme: dark)')
  if (appearance === 'system') return systemDark ? 'dark' : 'light'
  return appearance
}
