import test from 'node:test'
import assert from 'node:assert/strict'

import {
  API_CONFIG_STORAGE_KEY,
  clearApiConfig,
  loadApiConfig,
  saveApiConfig,
} from '../src/lib/apiConfigStorage.js'

function createStorage(initial = {}) {
  const values = new Map(Object.entries(initial))
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null },
    setItem(key, value) { values.set(key, value) },
    removeItem(key) { values.delete(key) },
  }
}

const fallback = { provider: 'minimax', apiKey: '', model: 'MiniMax-M2.1', preset: 'normal' }

test('API configuration survives a browser reload', () => {
  const storage = createStorage()
  const config = { provider: 'openai', apiKey: 'sk-example', model: 'gpt-5', preset: 'innovation' }

  assert.equal(saveApiConfig(config, { storage }), true)
  assert.deepEqual(loadApiConfig({ storage, fallback }), config)
})

test('invalid stored data falls back safely and can be cleared', () => {
  const storage = createStorage({ [API_CONFIG_STORAGE_KEY]: '{invalid-json' })
  assert.deepEqual(loadApiConfig({ storage, fallback }), fallback)
  assert.equal(clearApiConfig({ storage }), true)
  assert.equal(storage.getItem(API_CONFIG_STORAGE_KEY), null)
})

test('storage failures do not crash configuration flows', () => {
  const storage = {
    getItem() { throw new Error('blocked') },
    setItem() { throw new Error('full') },
    removeItem() { throw new Error('blocked') },
  }
  assert.deepEqual(loadApiConfig({ storage, fallback }), fallback)
  assert.equal(saveApiConfig(fallback, { storage }), false)
  assert.equal(clearApiConfig({ storage }), false)
})
