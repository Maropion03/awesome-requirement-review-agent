import test from 'node:test'
import assert from 'node:assert/strict'

import {
  API_CONFIG_STORAGE_KEY,
  clearApiConfig,
  loadApiConfig,
  resolveVisionModel,
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

const fallback = { apiFormat: 'openai_chat', baseUrl: 'https://api.openai.com/v1', apiKey: '', model: 'gpt-5.2', visionModel: '', preset: 'normal' }

test('API configuration survives a browser reload', () => {
  const storage = createStorage()
  const config = { apiFormat: 'openai_responses', baseUrl: 'https://api.example.com/v1', apiKey: 'sk-example', model: 'gpt-5', visionModel: 'gpt-5-mini', preset: 'innovation' }

  assert.equal(saveApiConfig(config, { storage }), true)
  assert.deepEqual(loadApiConfig({ storage, fallback }), config)
})

test('legacy provider configuration migrates to an API format and original official host', () => {
  const storage = createStorage({
    [API_CONFIG_STORAGE_KEY]: JSON.stringify({ provider: 'deepseek', apiKey: 'legacy-key', model: 'deepseek-chat', preset: 'normal' }),
  })
  assert.deepEqual(loadApiConfig({ storage, fallback }), {
    apiFormat: 'openai_chat',
    baseUrl: 'https://api.deepseek.com',
    apiKey: 'legacy-key',
    model: 'deepseek-chat',
    visionModel: '',
    preset: 'normal',
  })
})

test('GLM-5.3 on the official endpoint gets a vision-capable default without overriding explicit configuration', () => {
  assert.equal(resolveVisionModel({ baseUrl: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-5.3', visionModel: '' }), 'glm-4.6v-flash')
  assert.equal(resolveVisionModel({ baseUrl: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-5.3', visionModel: 'glm-4.6v' }), 'glm-4.6v')
  assert.equal(resolveVisionModel({ baseUrl: 'https://proxy.example.com/v1', model: 'glm-5.3', visionModel: '' }), 'glm-5.3')
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
