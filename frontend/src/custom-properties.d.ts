// Lets style={{ '--progress': '40%' }} type-check. Custom properties are the only thing style= may
// pass (scripts/check-tsx.ts enforces it), so every value comes from CSS.
import 'react'

declare module 'react' {
  interface CSSProperties {
    [property: `--${string}`]: string | number | undefined
  }
}
