export const DEFAULT_STATE = 'todo'
export const SUPPORTED_STATUSES = ['todo', 'accepted', 'ignored', 'fixed_pending_verify']

export function normalizeStatus(status) {
  return SUPPORTED_STATUSES.includes(status) ? status : DEFAULT_STATE
}

export function getIssueIdentifier(issue) {
  if (!issue || typeof issue !== 'object') return null
  return issue.issueKey || issue.displayId || issue.id || null
}

export function createIssueState(issues = []) {
  return issues.reduce((state, issue) => {
    const issueId = getIssueIdentifier(issue)
    if (!issueId) return state

    state[issueId] = {
      status: normalizeStatus(issue.status),
    }
    return state
  }, {})
}

export function updateIssueStatus(state = {}, issueId, status) {
  if (!issueId) return { ...state }

  return {
    ...state,
    [issueId]: {
      ...(state[issueId] || {}),
      status: normalizeStatus(status),
    },
  }
}

export function getIssueStatus(state = {}, issue = null) {
  const issueId = typeof issue === 'string' ? issue : getIssueIdentifier(issue)
  return state[issueId]?.status || DEFAULT_STATE
}

export function mergeIssueStatuses(currentState = {}, issues = []) {
  return issues.reduce((nextState, issue) => {
    const issueId = getIssueIdentifier(issue)
    if (!issueId) return nextState

    nextState[issueId] = {
      ...(currentState[issueId] || {}),
      status: getIssueStatus(currentState, issue),
    }
    return nextState
  }, {})
}

export function buildIssueExportItems(issues = [], issueState = {}) {
  return issues
    .map((issue) => {
      const issueId = getIssueIdentifier(issue)
      if (!issueId) return null

      return {
        ...issue,
        issueId,
        status: getIssueStatus(issueState, issue),
      }
    })
    .filter(Boolean)
}
