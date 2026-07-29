export const API_CONFIG_STORAGE_KEY = 'prd-review-byok-config-v1'

export function normalizeApiConfig(value = {}, fallback = {}) {
  return {
    provider: String(value.provider || fallback.provider || ''),
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
    return saved && typeof saved === 'object'
      ? normalizeApiConfig(saved, normalizedFallback)
      : normalizedFallback
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
