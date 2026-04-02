import test from 'node:test'
import assert from 'node:assert/strict'

import {
  formatHashRoute,
  normalizeHashRoute,
  parseHashRoute,
  resolveHashRoute,
  HASH_ROUTES,
} from '../src/lib/hashRoute.js'

test('parseHashRoute accepts known hash routes', () => {
  assert.equal(parseHashRoute('#/workbench'), 'workbench')
  assert.equal(parseHashRoute('#/report'), HASH_ROUTES.report)
  assert.equal(parseHashRoute('#assistant'), HASH_ROUTES.assistant)
  assert.equal(parseHashRoute('   #/assistant  '), HASH_ROUTES.assistant)
})

test('resolveHashRoute prefers the current hash and falls back safely', () => {
  assert.equal(
    resolveHashRoute({
      hash: '#/assistant',
      storedRoute: '#/report',
    }),
    HASH_ROUTES.assistant,
  )

  assert.equal(
    resolveHashRoute({
      hash: '',
      storedRoute: '#/assistant',
    }),
    HASH_ROUTES.assistant,
  )

  assert.equal(
    resolveHashRoute({
      hash: '#/unknown',
      storedRoute: 'also-unknown',
    }),
    HASH_ROUTES.report,
  )
})

test('formatHashRoute normalizes unknown values back to report', () => {
  assert.equal(formatHashRoute(HASH_ROUTES.assistant), '#/assistant')
  assert.equal(formatHashRoute('anything-else'), '#/report')
  assert.equal(normalizeHashRoute('anything-else'), HASH_ROUTES.report)
})
