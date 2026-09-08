export const PRODUCT_CONTEXT_STORAGE_KEY = 'prd-review-product-context-v1'

export const PRODUCT_CONTEXT_FIELDS = Object.freeze([
  { id: 'product_overview', label: '产品概览', maxLength: 5000 },
  { id: 'business_goals', label: '业务目标', maxLength: 4000 },
  { id: 'target_users', label: '目标用户', maxLength: 3000 },
  { id: 'success_metrics', label: '成功指标', maxLength: 3000 },
  { id: 'decisions_constraints', label: '历史决策与约束', maxLength: 5000 },
])

export function createEmptyProductContext() {
  return {
    enabled: true,
    product_overview: '',
    business_goals: '',
    target_users: '',
    success_metrics: '',
    decisions_constraints: '',
  }
}

export function normalizeProductContext(value = {}) {
  const normalized = createEmptyProductContext()
  normalized.enabled = value.enabled !== false
  for (const field of PRODUCT_CONTEXT_FIELDS) {
    normalized[field.id] = String(value[field.id] || '').slice(0, field.maxLength)
  }
  return normalized
}

export function getProductContextSummary(value = {}) {
  const normalized = normalizeProductContext(value)
  const activeFields = PRODUCT_CONTEXT_FIELDS.filter((field) => normalized[field.id].trim())
  return {
    enabled: normalized.enabled,
    fieldCount: activeFields.length,
    totalCharacters: activeFields.reduce((total, field) => total + normalized[field.id].trim().length, 0),
    labels: activeFields.map((field) => field.label),
  }
}

export function buildProductContextPayload(value = {}) {
  const normalized = normalizeProductContext(value)
  if (!normalized.enabled || !getProductContextSummary(normalized).fieldCount) return null
  return normalized
}

export function loadProductContext({ storage } = {}) {
  if (!storage?.getItem) return createEmptyProductContext()
  try {
    const saved = JSON.parse(storage.getItem(PRODUCT_CONTEXT_STORAGE_KEY) || 'null')
    return saved && typeof saved === 'object' ? normalizeProductContext(saved) : createEmptyProductContext()
  } catch {
    return createEmptyProductContext()
  }
}

export function saveProductContext(value, { storage } = {}) {
  if (!storage?.setItem) return false
  try {
    storage.setItem(PRODUCT_CONTEXT_STORAGE_KEY, JSON.stringify(normalizeProductContext(value)))
    return true
  } catch {
    return false
  }
}

export function clearProductContext({ storage } = {}) {
  if (!storage?.removeItem) return false
  try {
    storage.removeItem(PRODUCT_CONTEXT_STORAGE_KEY)
    return true
  } catch {
    return false
  }
}
