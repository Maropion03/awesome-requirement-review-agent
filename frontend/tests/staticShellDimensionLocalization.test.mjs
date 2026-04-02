import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const source = readFileSync(resolve(process.cwd(), 'first page code_integrated.html'), 'utf8')

test('static shell localizes backend dimension keys before rendering', () => {
  assert.match(source, /function getDisplayDimensionName\(/)
  assert.match(source, /priority_consistency["']?\s*:\s*["']优先级一致性["']/)
  assert.match(source, /getDisplayDimensionName\(selectedIssue\.dimension\)/)
  assert.match(source, /getDisplayDimensionName\(item\.dimension\)/)
  assert.match(source, /getDisplayDimensionName\(issue\.dimension\)/)
})
