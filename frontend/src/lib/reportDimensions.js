export function toggleDimensionExpansion(expandedDimensions = [], dimensionName) {
  if (!dimensionName) return [...expandedDimensions]

  const current = Array.isArray(expandedDimensions) ? expandedDimensions : []
  if (current.includes(dimensionName)) {
    return current.filter((name) => name !== dimensionName)
  }

  return [...current, dimensionName]
}

export function isDimensionExpanded(expandedDimensions = [], dimensionName) {
  if (!dimensionName) return false
  return Array.isArray(expandedDimensions) && expandedDimensions.includes(dimensionName)
}
