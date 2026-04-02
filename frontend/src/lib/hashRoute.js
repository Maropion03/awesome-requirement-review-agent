export const HASH_ROUTES = Object.freeze({
  workbench: 'workbench',
  report: 'report',
  assistant: 'assistant',
})

export function normalizeHashRoute(route) {
  if (route === HASH_ROUTES.workbench) return HASH_ROUTES.workbench
  if (route === HASH_ROUTES.assistant) return HASH_ROUTES.assistant
  return HASH_ROUTES.report
}

export function parseHashRoute(hash) {
  if (typeof hash !== 'string') return null

  const trimmed = hash.trim()
  if (!trimmed) return null

  const normalized = trimmed.replace(/^#/, '').replace(/^\/+/, '')
  if (
    normalized === HASH_ROUTES.workbench ||
    normalized === HASH_ROUTES.report ||
    normalized === HASH_ROUTES.assistant
  ) {
    return normalized
  }

  return null
}

export function formatHashRoute(route) {
  return `#/${normalizeHashRoute(route)}`
}

export function resolveHashRoute({ hash, storedRoute, fallback = HASH_ROUTES.report } = {}) {
  return (
    parseHashRoute(hash) ||
    parseHashRoute(storedRoute) ||
    normalizeHashRoute(fallback)
  )
}
