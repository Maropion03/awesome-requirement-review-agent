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

test('ReportViewer preserves the formal report hierarchy', () => {
  const source = readFileSync(resolve(process.cwd(), 'src/components/ReportViewer.vue'), 'utf8')

  assert.match(source, /class="report-hero"/)
  assert.match(source, /class="score-ring"/)
  assert.match(source, /结论摘要/)
  assert.match(source, /class="dimension-strip"/)
  assert.match(source, /class="dimension-detail"/)
  assert.match(source, /class="issues-section"/)
  assert.match(source, /class="evidence-quote"/)
  assert.doesNotMatch(source, /class="summary-grid"/)
})
