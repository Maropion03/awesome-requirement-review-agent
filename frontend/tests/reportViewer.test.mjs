import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import {
  isDimensionExpanded,
  toggleDimensionExpansion,
} from '../src/lib/reportDimensions.js'

test('toggleDimensionExpansion keeps each dimension independent', () => {
  let expanded = []

  expanded = toggleDimensionExpansion(expanded, '需求完整性')
  assert.deepEqual(expanded, ['需求完整性'])
  assert.equal(isDimensionExpanded(expanded, '需求完整性'), true)

  expanded = toggleDimensionExpansion(expanded, '需求合理性')
  assert.deepEqual(expanded, ['需求完整性', '需求合理性'])
  assert.equal(isDimensionExpanded(expanded, '需求合理性'), true)

  expanded = toggleDimensionExpansion(expanded, '需求完整性')
  assert.deepEqual(expanded, ['需求合理性'])
  assert.equal(isDimensionExpanded(expanded, '需求完整性'), false)
})

test('ReportViewer uses low fidelity sections for dimension cards', () => {
  const source = readFileSync(resolve(process.cwd(), 'src/components/ReportViewer.vue'), 'utf8')

  assert.match(source, /评分说明/)
  assert.match(source, /主要问题/)
  assert.match(source, /修改方向/)
})
