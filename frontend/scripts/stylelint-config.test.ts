// @vitest-environment node
import { resolve } from 'node:path'
import stylelint from 'stylelint'
import { describe, expect, it } from 'vitest'

async function rules(file: string, code: string) {
  const { results } = await stylelint.lint({
    code,
    codeFilename: resolve(file),
    configFile: resolve('stylelint.config.js'),
  })
  return results[0].warnings.map((warning) => warning.rule)
}

const module = 'src/components/A/A.module.css'

describe('raw values', () => {
  it('rejects a colour function, a hex colour inside a gradient and a raw radius in a component', async () => {
    expect(await rules(module, '.a {\n  color: rgb(0 0 0);\n}\n')).toContain('scale-unlimited/declaration-strict-value')
    expect(await rules(module, '.a {\n  background: linear-gradient(#fff, var(--x));\n}\n')).toContain('color-no-hex')
    expect(await rules(module, '.a {\n  border-radius: 7px;\n}\n')).toContain('scale-unlimited/declaration-strict-value')
  })
})
