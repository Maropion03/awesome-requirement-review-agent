const EXPORTABLE_STATUSES = new Set(['accepted', 'fixed_pending_verify'])

function normalizeFileName(fileName = 'prd-review-suggestions.md') {
  const trimmed = String(fileName || '').trim()
  return trimmed || 'prd-review-suggestions.md'
}

function formatStatus(status) {
  const labels = {
    accepted: '已采纳',
    fixed_pending_verify: '待复核',
  }

  return labels[status] || status || '待处理'
}

export function buildSuggestionExport({ issues = [] } = {}) {
  const exportableIssues = issues.filter((issue) => EXPORTABLE_STATUSES.has(issue.status))

  if (!exportableIssues.length) {
    return '# 修改建议导出\n\n当前没有已采纳或待复核的问题可导出。'
  }

  return [
    '# 修改建议导出',
    '',
    ...exportableIssues.flatMap((issue) => ([
      `## ${issue.displayId || issue.issueId || issue.id || 'ISSUE'} ${issue.title || '未命名问题'}`,
      `- 当前状态：${formatStatus(issue.status)}`,
      `- 维度：${issue.dimension || '未标注维度'}`,
      `- 问题描述：${issue.description || '未提供问题描述'}`,
      `- 修改建议：${issue.suggestion || '未提供修改建议'}`,
      '',
    ])),
  ].join('\n').trim()
}

export function buildExportPayload({ fileName, issues = [] } = {}) {
  return {
    fileName: normalizeFileName(fileName),
    mimeType: 'text/markdown;charset=utf-8',
    content: buildSuggestionExport({ issues }),
  }
}
