// WCAG contrast ratio between two hex colours, from 1 (the same) to 21 (black on white). Used by the
// contrast test and by the review page, so both report the same numbers.

function channel(value: number): number {
  const scaled = value / 255
  return scaled <= 0.04045 ? scaled / 12.92 : ((scaled + 0.055) / 1.055) ** 2.4
}

function luminance(hex: string): number {
  const digits = hex.replace('#', '')
  const full = digits.length === 3 ? digits.split('').map((digit) => digit + digit).join('') : digits
  const [red, green, blue] = [0, 2, 4].map((start) => channel(parseInt(full.slice(start, start + 2), 16)))
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue
}

export function contrast(foreground: string, background: string): number {
  const [lighter, darker] = [luminance(foreground), luminance(background)].sort((a, b) => b - a)
  return (lighter + 0.05) / (darker + 0.05)
}
