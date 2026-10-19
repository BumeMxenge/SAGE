// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { checkSource } from './check-tsx.ts'

const src = '/p/src'
const messages = (file: string, code: string) => checkSource(`${src}/${file}`, code, src).map((v) => v.message)

describe('style=', () => {
  it('rejects a size', () => {
    expect(messages('components/A/A.tsx', 'const a = <div style={{ width: 10 }} />')).toHaveLength(1)
  })

  it('accepts a custom property', () => {
    expect(messages('components/A/A.tsx', "const a = <div style={{ '--progress': 10 }} />")).toEqual([])
  })
})

describe('re-exports', () => {
  it('rejects export from, named or star', () => {
    expect(messages('components/A/A.tsx', "export { B } from './B.tsx'")).toHaveLength(1)
    expect(messages('components/A/A.tsx', "export * from './B.tsx'")).toHaveLength(1)
  })

  it('accepts exporting something defined here', () => {
    expect(messages('components/A/A.tsx', 'const a = 1\nexport { a }')).toEqual([])
  })
})

describe('boundaries', () => {
  it('rejects shared code importing a feature, by either kind of path', () => {
    expect(messages('components/A/A.tsx', "import { x } from '@/features/auth/x.ts'")).toHaveLength(1)
    expect(messages('lib/y.ts', "import { x } from '../features/auth/x.ts'")).toHaveLength(1)
  })

  it('rejects one feature importing another, but not itself', () => {
    expect(messages('features/a/A.ts', "import { b } from '@/features/b/B.ts'")).toHaveLength(1)
    expect(messages('features/a/A.ts', "import { b } from '../b/B.ts'")).toHaveLength(1)
    expect(messages('features/a/A.ts', "import { a } from './helper.ts'")).toEqual([])
    expect(messages('features/a/A.ts', "import { c } from '@/components/C/C.tsx'")).toEqual([])
  })

  it('lets the app frame import features', () => {
    expect(messages('app/App.tsx', "import { x } from '../features/auth/x.ts'")).toEqual([])
  })
})
