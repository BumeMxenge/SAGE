// The checks oxlint can't make on its own, run by `npm run lint`:
//   1. style= may only pass custom properties ('--name'), so every size and colour comes from a token
//   2. no re-exports (`export … from`), so every import names the file that defines the thing
//   3. no import crosses a boundary: shared code never imports a feature, and features never import
//      each other
import { readdirSync, readFileSync } from 'node:fs'
import { dirname, join, relative, resolve, sep } from 'node:path'
import ts from 'typescript'

export type Violation = { file: string; line: number; message: string }

const sharedFolders = ['components', 'lib', 'styles']

// Where an import points, as a path inside src/, or undefined for a package such as 'react'
function target(specifier: string, file: string, srcRoot: string): string | undefined {
  if (specifier.startsWith('@/')) return specifier.slice(2)
  if (specifier.startsWith('.')) return relative(srcRoot, resolve(dirname(file), specifier)).split(sep).join('/')
  return undefined
}

function boundaryMessage(from: string, to: string): string | undefined {
  const [fromTop, fromFeature] = from.split('/')
  const [toTop, toFeature] = to.split('/')
  if (toTop !== 'features') return undefined
  if (sharedFolders.includes(fromTop)) return 'shared code must not import a feature'
  if (fromTop === 'features' && fromFeature !== toFeature) return 'a feature must not import another feature'
  return undefined
}

export function checkSource(file: string, text: string, srcRoot: string): Violation[] {
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
  const from = relative(srcRoot, file).split(sep).join('/')
  const found: Violation[] = []
  const report = (node: ts.Node, message: string) =>
    found.push({ file, line: source.getLineAndCharacterOfPosition(node.getStart()).line + 1, message })

  function checkImport(node: ts.Node, specifier: string) {
    const to = target(specifier, file, srcRoot)
    const message = to && boundaryMessage(from, to)
    if (message) report(node, `${message}: ${specifier}`)
  }

  function visit(node: ts.Node) {
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)) {
      checkImport(node, node.moduleSpecifier.text)
    }
    if (ts.isExportDeclaration(node) && node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier)) {
      report(node, `re-export: import from the file that defines it instead: ${node.moduleSpecifier.text}`)
    }
    if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      const [argument] = node.arguments
      if (ts.isStringLiteralLike(argument)) checkImport(node, argument.text)
    }
    if (ts.isJsxAttribute(node) && node.name.getText() === 'style' && !passesOnlyCustomProperties(node)) {
      report(node, "style= may only pass custom properties, such as style={{ '--progress': value }}")
    }
    ts.forEachChild(node, visit)
  }
  visit(source)
  return found
}

function passesOnlyCustomProperties(attribute: ts.JsxAttribute): boolean {
  const value = attribute.initializer
  if (!value || !ts.isJsxExpression(value) || !value.expression) return false
  const object = value.expression
  if (!ts.isObjectLiteralExpression(object)) return false
  return object.properties.every(
    (property) =>
      ts.isPropertyAssignment(property) &&
      ts.isStringLiteral(property.name) &&
      property.name.text.startsWith('--'),
  )
}

function sourceFiles(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const path = join(folder, entry.name)
    if (entry.isDirectory()) return sourceFiles(path)
    return /\.(ts|tsx)$/.test(entry.name) ? [path] : []
  })
}

if (import.meta.main) {
  const srcRoot = resolve(import.meta.dirname, '../src')
  const violations = sourceFiles(srcRoot).flatMap((file) => checkSource(file, readFileSync(file, 'utf8'), srcRoot))
  for (const { file, line, message } of violations) console.error(`${relative(process.cwd(), file)}:${line}  ${message}`)
  process.exit(violations.length ? 1 : 0)
}
