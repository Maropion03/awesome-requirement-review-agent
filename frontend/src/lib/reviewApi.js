const DEFAULT_API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || '/api'

export const PROVIDER_FALLBACKS = [
  { id: 'minimax', name: 'MiniMax', protocol: 'openai', default_model: 'MiniMax-M2.7', key_hint: 'MiniMax API Key' },
  { id: 'openai', name: 'OpenAI', protocol: 'openai', default_model: 'gpt-5.2', key_hint: 'sk-...' },
  { id: 'anthropic', name: 'Anthropic', protocol: 'anthropic', default_model: 'claude-sonnet-5', key_hint: 'sk-ant-...' },
  { id: 'deepseek', name: 'DeepSeek', protocol: 'openai', default_model: 'deepseek-v4-flash', key_hint: 'sk-...' },
  { id: 'gemini', name: 'Google Gemini', protocol: 'openai', default_model: 'gemini-3.6-flash', key_hint: 'Google AI API Key' },
  { id: 'openrouter', name: 'OpenRouter', protocol: 'openai', default_model: '~openai/gpt-latest', key_hint: 'sk-or-v1-...' },
]

export function createApiUrl(baseUrl = DEFAULT_API_BASE_URL, path = '') {
  const normalizedBaseUrl = String(baseUrl).replace(/\/+$/, '')
  const normalizedPath = String(path).replace(/^\/+/, '')
  return `${normalizedBaseUrl}/${normalizedPath}`
}

export async function requestJsonWithFallback({
  baseUrl = DEFAULT_API_BASE_URL,
  path,
  options = {},
  fetchImpl = fetch,
}) {
  return fetchImpl(createApiUrl(baseUrl, path), options)
}

async function parseJsonResponse(response) {
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const rawDetail = data?.detail
    const detail = Array.isArray(rawDetail)
      ? rawDetail.map((item) => item?.msg || String(item)).join('；')
      : rawDetail || `Request failed with status ${response.status}`
    throw new Error(detail)
  }

  return data
}

export async function loadProviderCatalog({
  baseUrl = DEFAULT_API_BASE_URL,
  fetchImpl = fetch,
} = {}) {
  const response = await requestJsonWithFallback({
    baseUrl,
    path: '/providers',
    fetchImpl,
  })
  return parseJsonResponse(response)
}

export async function validateProvider({
  baseUrl = DEFAULT_API_BASE_URL,
  provider,
  apiKey,
  model,
  fetchImpl = fetch,
}) {
  const response = await requestJsonWithFallback({
    baseUrl,
    path: '/providers/validate',
    options: {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider,
        api_key: apiKey,
        model,
      }),
    },
    fetchImpl,
  })

  return parseJsonResponse(response)
}

function dispatchReviewEvent(payload, callbacks) {
  const handlers = {
    connected: callbacks.onConnected,
    dimension_start: callbacks.onDimensionStart,
    dimension_complete: callbacks.onDimensionComplete,
    streaming: callbacks.onStreaming,
    complete: (value) => callbacks.onComplete?.(value.report || value),
    error: callbacks.onError,
  }
  handlers[payload.event]?.(payload)
}

export async function startReviewStream({
  baseUrl = DEFAULT_API_BASE_URL,
  file,
  provider,
  apiKey,
  model,
  preset,
  signal,
  fetchImpl = fetch,
  onConnected,
  onDimensionStart,
  onDimensionComplete,
  onStreaming,
  onComplete,
  onError,
}) {
  const body = new FormData()
  body.append('file', file)
  body.append('provider', provider)
  body.append('api_key', apiKey)
  body.append('model', model)
  body.append('preset', preset)

  const response = await fetchImpl(createApiUrl(baseUrl, '/review/run'), {
    method: 'POST',
    body,
    signal,
  })
  if (!response.ok) return parseJsonResponse(response)
  if (!response.body?.getReader) throw new Error('当前浏览器不支持流式响应')

  const callbacks = { onConnected, onDimensionStart, onDimensionComplete, onStreaming, onComplete, onError }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let fatalError = null

  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.trim()) continue
      const payload = JSON.parse(line)
      dispatchReviewEvent(payload, callbacks)
      if (payload.event === 'error') fatalError = new Error(payload.message || '评审失败')
    }
    if (done) break
  }
  if (buffer.trim()) dispatchReviewEvent(JSON.parse(buffer), callbacks)
  if (fatalError) throw fatalError
}

export function createBaseDimensions() {
  return [
    { id: 1, name: '需求完整性', status: 'pending' },
    { id: 2, name: '需求合理性', status: 'pending' },
    { id: 3, name: '用户价值', status: 'pending' },
    { id: 4, name: '技术可行性', status: 'pending' },
    { id: 5, name: '实现风险', status: 'pending' },
    { id: 6, name: '优先级一致性', status: 'pending' },
  ]
}

function mapRecommendation(recommendation) {
  const labels = {
    APPROVE: '通过',
    MODIFY: '修改后通过',
    REJECT: '驳回',
    PENDING: '进行中',
  }

  return labels[recommendation] || recommendation || '尚未生成'
}

function mapSeverity(severity) {
  const labels = {
    HIGH: '高',
    MEDIUM: '中',
    LOW: '低',
  }

  return labels[severity] || severity || '未知'
}

function formatScore(score) {
  if (score == null || Number.isNaN(Number(score))) return '--'
  return String(score)
}

function formatWeight(weight) {
  if (weight == null || Number.isNaN(Number(weight))) return '--'
  return `${Math.round(Number(weight) * 100)}%`
}

function normalizeIssue(issue = {}, index = 0) {
  const severity = issue.severity || 'LOW'
  const displayId = issue.display_id || issue.displayId || issue.id || `ISSUE-${index + 1}`
  const issueKey = issue.issue_key || issue.issueKey || null
  return {
    id: issue.id || displayId,
    displayId,
    issueKey,
    level: mapSeverity(severity),
    severity,
    title: issue.title || issue.description || '未命名问题',
    dimension: issue.dimension || '未标注维度',
    description: issue.description || issue.reasoning || '未提供问题描述',
    suggestion: issue.suggestion || '未提供修改建议',
    sourceQuote: issue.source_quote || issue.sourceQuote || '',
    sourceSection: issue.source_section || issue.sourceSection || '',
    sourceLocator: issue.source_locator || issue.sourceLocator || '',
  }
}

function summarizeText(text = '', maxLength = 28) {
  const compact = String(text).replace(/\s+/g, ' ').trim()
  if (!compact) return ''
  return compact.length > maxLength ? `${compact.slice(0, maxLength - 1)}…` : compact
}

function summarizeDimension(issues = [], reasoning = '') {
  const titles = issues
    .map((issue) => issue.title)
    .filter(Boolean)
    .slice(0, 2)

  if (titles.length) {
    return summarizeText(titles.join('，'))
  }

  return summarizeText(reasoning || '当前维度暂无明显问题')
}

function buildActionHints(issues = []) {
  const hints = []

  for (const issue of issues) {
    const suggestion = issue.suggestion
    if (!suggestion || suggestion === '未提供修改建议' || hints.includes(suggestion)) {
      continue
    }
    hints.push(suggestion)
    if (hints.length === 3) break
  }

  if (hints.length) return hints
  return ['结合该维度补充更明确的描述、边界和验收口径。']
}

function getDimensionStatus(score, issuesCount, highIssuesCount) {
  const numericScore = Number(score)

  if (highIssuesCount > 0 || (!Number.isNaN(numericScore) && numericScore < 6)) {
    return { label: '需重点关注', tone: 'danger' }
  }

  if (issuesCount > 0 || Number.isNaN(numericScore) || numericScore < 8) {
    return { label: '需要补强', tone: 'warning' }
  }

  return { label: '表现良好', tone: 'good' }
}

function buildDimensionCards(dimensionScores = [], issues = []) {
  const normalizedIssues = issues.map((issue, index) => normalizeIssue(issue, index))

  return (dimensionScores || []).map((dimension) => {
    const dimensionIssues = normalizedIssues.filter((issue) => issue.dimension === (dimension.dimension || '未命名维度'))
    const highIssuesCount = dimensionIssues.filter((issue) => issue.severity === 'HIGH').length
    const status = getDimensionStatus(dimension.score, dimension.issues_count || 0, highIssuesCount)

    return {
      dimension: dimension.dimension || '未命名维度',
      score: formatScore(dimension.score),
      weightLabel: formatWeight(dimension.weight),
      issuesCount: dimension.issues_count || 0,
      highIssuesCount,
      statusLabel: status.label,
      statusTone: status.tone,
      summary: summarizeDimension(dimensionIssues, dimension.reasoning),
      topIssues: dimensionIssues.slice(0, 3),
      actionHints: buildActionHints(dimensionIssues),
      reasoning: dimension.reasoning || '未生成分析说明',
    }
  })
}

function buildIssueGroups(issues = []) {
  const groups = new Map()

  issues.forEach((issue, index) => {
    const severity = issue.severity || 'LOW'
    if (!groups.has(severity)) {
      groups.set(severity, {
        severity,
        label: `${mapSeverity(severity)}优先级`,
        count: 0,
        issues: [],
      })
    }

    const group = groups.get(severity)
    group.issues.push(normalizeIssue(issue, index))
    group.count = group.issues.length
  })

  return ['HIGH', 'MEDIUM', 'LOW']
    .filter((severity) => groups.has(severity))
    .map((severity) => groups.get(severity))
}

export function createEmptyReportViewModel() {
  return {
    score: '--',
    suggestion: '尚未生成',
    summary: '评审完成后将在这里展示综合结论。',
    dimensionScores: [],
    issueGroups: [],
    issues: [],
    rawReport: null,
  }
}

export function mapReportToViewModel(report = {}) {
  const normalizedIssues = (report.issues || []).map((issue, index) => normalizeIssue(issue, index))

  return {
    score: formatScore(report.total_score),
    suggestion: mapRecommendation(report.recommendation),
    summary: report.summary || '未生成摘要',
    dimensionScores: buildDimensionCards(report.dimension_scores || [], report.issues || []),
    issueGroups: buildIssueGroups(report.issues || []),
    issues: normalizedIssues,
    rawReport: report,
  }
}
