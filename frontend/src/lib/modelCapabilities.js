const KNOWN_TEXT_ONLY_MODELS = Object.freeze([
  {
    pattern: /^glm-5\.3(?:-|$)/i,
    label: 'GLM-5.3 系列',
    sourceUrl: 'https://docs.bigmodel.cn/cn/guide/models/text/glm-5.3',
  },
])

export function detectModelCapability(model) {
  const normalizedModel = String(model || '').trim()
  const match = KNOWN_TEXT_ONLY_MODELS.find((candidate) => candidate.pattern.test(normalizedModel))
  if (!match) return { capability: 'unknown', model: normalizedModel }
  return {
    capability: 'text_only',
    model: normalizedModel,
    family: match.label,
    sourceUrl: match.sourceUrl,
  }
}

export function isKnownTextOnlyModel(model) {
  return detectModelCapability(model).capability === 'text_only'
}

export function shouldConfirmTextOnlyPdfReview({ fileName, model } = {}) {
  return /\.pdf$/i.test(String(fileName || '').trim()) && isKnownTextOnlyModel(model)
}
