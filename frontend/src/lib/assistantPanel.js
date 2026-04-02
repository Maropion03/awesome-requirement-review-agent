export function createAssistantState() {
  return {
    chatMessages: [],
    selectedIssue: null,
    suggestedActions: [],
    sourceRefs: [],
    assistantStatus: 'unavailable',
    responseMode: 'report_level',
  }
}

export function buildAssistantSnapshot({ report, runState, selectedIssue }) {
  return {
    score: report?.score ?? '--',
    suggestion: report?.suggestion ?? '尚未生成',
    summary: report?.summary ?? '评审完成后将在这里显示结论。',
    status: runState?.status ?? 'idle',
    progress: runState?.progress ?? 0,
    currentDimension: runState?.current_dimension ?? null,
    selectedIssue: selectedIssue ?? null,
  }
}

export function normalizeChatResponse(response = {}) {
  return {
    message: response.message || '',
    responseMode: response.response_mode || 'report_level',
    assistantStatus: response.assistant_status || 'unavailable',
    selectedIssue: normalizeIssueRef(response.selected_issue),
    suggestedActions: Array.isArray(response.suggested_actions) ? response.suggested_actions : [],
    sourceRefs: Array.isArray(response.source_refs) ? response.source_refs : [],
    targetIssueId: response.target_issue_id || null,
    runState: response.run_state || {},
  }
}

function normalizeIssueRef(issue = null) {
  if (!issue || typeof issue !== 'object') return null

  return {
    issueKey: issue.issue_key || issue.issueKey || null,
    displayId: issue.display_id || issue.displayId || issue.id || null,
    id: issue.id || issue.display_id || issue.displayId || null,
    title: issue.title || '',
    dimension: issue.dimension || '',
    severity: issue.severity || '',
  }
}

export function flattenIssues(report = {}) {
  const issues = []
  for (const group of report.issueGroups || []) {
    for (const issue of group.issues || []) {
      issues.push(issue)
    }
  }
  return issues
}

export function findIssueById(report = {}, issueId) {
  if (!issueId) return null
  const target = normalizeIssueIdentifier(issueId)
  return flattenIssues(report).find((issue) => {
    return [
      issue.id,
      issue.displayId,
      issue.issueKey,
    ].some((candidate) => normalizeIssueIdentifier(candidate) === target)
  }) || null
}

function normalizeIssueIdentifier(value) {
  return String(value || '').trim().replace(/\s+/g, '').replace(/【/g, '[').replace(/】/g, ']').replace(/^\[|\]$/g, '').toUpperCase()
}
