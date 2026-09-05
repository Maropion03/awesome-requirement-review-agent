export const API_CONFIG_STORAGE_KEY = 'prd-review-byok-config-v1'

const LEGACY_PROVIDER_MIGRATION = Object.freeze({
  minimax: { apiFormat: 'openai_chat', baseUrl: 'https://api.minimax.io/v1' },
  openai: { apiFormat: 'openai_chat', baseUrl: 'https://api.openai.com/v1' },
  anthropic: { apiFormat: 'anthropic_messages', baseUrl: 'https://api.anthropic.com' },
  deepseek: { apiFormat: 'openai_chat', baseUrl: 'https://api.deepseek.com' },
  gemini: { apiFormat: 'openai_chat', baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai' },
  openrouter: { apiFormat: 'openai_chat', baseUrl: 'https://openrouter.ai/api/v1' },
})

export function normalizeApiConfig(value = {}, fallback = {}) {
  const legacy = LEGACY_PROVIDER_MIGRATION[String(value.provider || '').toLowerCase()] || {}
  return {
    apiFormat: String(value.apiFormat || legacy.apiFormat || fallback.apiFormat || 'openai_chat'),
    baseUrl: String(value.baseUrl || legacy.baseUrl || fallback.baseUrl || 'https://api.openai.com/v1'),
    apiKey: String(value.apiKey || fallback.apiKey || ''),
    model: String(value.model || fallback.model || ''),
    preset: String(value.preset || fallback.preset || 'normal'),
  }
}

export function loadApiConfig({ storage, fallback = {} } = {}) {
  const normalizedFallback = normalizeApiConfig(fallback)
  if (!storage?.getItem) return normalizedFallback
  try {
    const saved = JSON.parse(storage.getItem(API_CONFIG_STORAGE_KEY) || 'null')
    return saved && typeof saved === 'object' ? normalizeApiConfig(saved, normalizedFallback) : normalizedFallback
  } catch {
    return normalizedFallback
  }
}

export function saveApiConfig(config, { storage } = {}) {
  if (!storage?.setItem) return false
  try {
    storage.setItem(API_CONFIG_STORAGE_KEY, JSON.stringify(normalizeApiConfig(config)))
    return true
  } catch {
    return false
  }
}

export function clearApiConfig({ storage } = {}) {
  if (!storage?.removeItem) return false
  try {
    storage.removeItem(API_CONFIG_STORAGE_KEY)
    return true
  } catch {
    return false
  }
}
