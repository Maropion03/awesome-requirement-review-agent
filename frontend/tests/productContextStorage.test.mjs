import test from 'node:test'
import assert from 'node:assert/strict'

import {
  PRODUCT_CONTEXT_STORAGE_KEY,
  buildProductContextPayload,
  clearProductContext,
  createEmptyProductContext,
  getProductContextSummary,
  loadProductContext,
  saveProductContext,
} from '../src/lib/productContextStorage.js'

function createStorage() {
  const values = new Map()
  return {
    getItem(key) { return values.get(key) || null },
    setItem(key, value) { values.set(key, value) },
    removeItem(key) { values.delete(key) },
  }
}

test('product context persists locally and exposes an explicit summary', () => {
  const storage = createStorage()
  const context = { ...createEmptyProductContext(), product_overview: '客服产品', business_goals: '提升一次解决率' }
  assert.equal(saveProductContext(context, { storage }), true)
  assert.deepEqual(loadProductContext({ storage }), context)
  assert.deepEqual(getProductContextSummary(context), {
    enabled: true,
    fieldCount: 2,
    totalCharacters: 11,
    labels: ['产品概览', '业务目标'],
  })
  assert.ok(storage.getItem(PRODUCT_CONTEXT_STORAGE_KEY))
})

test('disabled or empty product context is omitted from the review payload', () => {
  assert.equal(buildProductContextPayload(createEmptyProductContext()), null)
  assert.equal(buildProductContextPayload({ ...createEmptyProductContext(), enabled: false, product_overview: '已保存但停用' }), null)
  assert.equal(buildProductContextPayload({ ...createEmptyProductContext(), product_overview: '启用的背景' }).product_overview, '启用的背景')
})

test('product context can be cleared without affecting other browser storage', () => {
  const storage = createStorage()
  saveProductContext({ product_overview: '背景' }, { storage })
  assert.equal(clearProductContext({ storage }), true)
  assert.deepEqual(loadProductContext({ storage }), createEmptyProductContext())
})
