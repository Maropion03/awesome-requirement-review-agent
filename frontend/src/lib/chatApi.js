import { requestJsonWithFallback } from './reviewApi.js'

const DEFAULT_API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || '/api'

async function parseJsonResponse(response) {
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = data?.detail || `Request failed with status ${response.status}`
    throw new Error(detail)
  }

  return data
}

export async function sendChatMessage({
  baseUrl = DEFAULT_API_BASE_URL,
  sessionId,
  message,
  selectedIssueId = null,
  contextMode = 'default',
  fetchImpl = fetch,
}) {
  const response = await requestJsonWithFallback({
    baseUrl,
    path: '/review/chat',
    options: {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        selected_issue_id: selectedIssueId,
        context_mode: contextMode,
      }),
    },
    fetchImpl,
  })

  return parseJsonResponse(response)
}
