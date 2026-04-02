const DEFAULT_API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || '/api'
const DEV_FALLBACK_API_BASE_URL = 'http://127.0.0.1:8005/api'

export function createApiUrl(baseUrl = DEFAULT_API_BASE_URL, path = '') {
  const normalizedBaseUrl = String(baseUrl).replace(/\/+$/, '')
  const normalizedPath = String(path).replace(/^\/+/, '')
  return `${normalizedBaseUrl}/${normalizedPath}`
}

function shouldUseDevFallback(baseUrl) {
  return String(baseUrl).startsWith('/')
}

function isStructuredJsonResponse(response) {
  const contentType = response?.headers?.get?.('content-type') || ''
  return contentType.toLowerCase().includes('application/json')
}

export async function requestJsonWithFallback({
  baseUrl = DEFAULT_API_BASE_URL,
  path,
  options = {},
  fetchImpl = fetch,
}) {
  const primaryUrl = createApiUrl(baseUrl, path)

  try {
    const response = await fetchImpl(primaryUrl, options)

    if (
      response.status === 404 &&
      shouldUseDevFallback(baseUrl) &&
      !isStructuredJsonResponse(response)
    ) {
      return fetchImpl(createApiUrl(DEV_FALLBACK_API_BASE_URL, path), options)
    }

    return response
  } catch (error) {
    if (!shouldUseDevFallback(baseUrl)) {
      throw error
    }

    return fetchImpl(createApiUrl(DEV_FALLBACK_API_BASE_URL, path), options)
  }
}

async function parseJsonResponse(response) {
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = data?.detail || `Request failed with status ${response.status}`
    throw new Error(detail)
  }

  return data
}

export async function uploadPrd({
  baseUrl = DEFAULT_API_BASE_URL,
  file,
  fetchImpl = fetch,
}) {
  const body = new FormData()
  body.append('file', file)

  const response = await requestJsonWithFallback({
    baseUrl,
    path: '/review/upload',
    options: {
      method: 'POST',
      body,
    },
    fetchImpl,
  })

  return parseJsonResponse(response)
}

export async function startReview({
  baseUrl = DEFAULT_API_BASE_URL,
  sessionId,
  preset,
  fetchImpl = fetch,
}) {
  const response = await requestJsonWithFallback({
    baseUrl,
    path: '/review/start',
    options: {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        preset,
      }),
    },
    fetchImpl,
  })

  return parseJsonResponse(response)
}

export function createReviewStream({
  baseUrl = DEFAULT_API_BASE_URL,
  sessionId,
  EventSourceImpl = EventSource,
  onConnected,
  onDimensionStart,
  onDimensionComplete,
  onStreaming,
  onComplete,
  onError,
}) {
  const stream = new EventSourceImpl(createApiUrl(baseUrl, `/review/stream/${sessionId}`))
  const CONNECTING_STATE = EventSourceImpl.CONNECTING ?? 0
  const CLOSED_STATE = EventSourceImpl.CLOSED ?? 2

  stream.addEventListener('connected', (event) => {
    onConnected?.(JSON.parse(event.data))
  })

  stream.addEventListener('dimension_start', (event) => {
    onDimensionStart?.(JSON.parse(event.data))
  })

  stream.addEventListener('dimension_complete', (event) => {
    onDimensionComplete?.(JSON.parse(event.data))
  })

  stream.addEventListener('streaming', (event) => {
    onStreaming?.(JSON.parse(event.data))
  })

  stream.addEventListener('complete', (event) => {
    const payload = JSON.parse(event.data)
    onComplete?.(payload.report || payload)
  })

  stream.addEventListener('error', (event) => {
    try {
      const payload = JSON.parse(event.data)
      onError?.({
        ...payload,
        recoverable: false,
      })
    } catch {
      if (stream.readyState === CLOSED_STATE) {
        onError?.({ message: '评审连接已关闭', recoverable: false })
        return
      }

      if (stream.readyState === CONNECTING_STATE) {
        onError?.({ message: '评审连接中断，正在重连', recoverable: true })
        return
      }

      onError?.({ message: '评审连接异常', recoverable: true })
    }
  })

  return stream
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
