import { requestJsonWithFallback } from './reviewApi.js'

const DEFAULT_API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || '/api'

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

export async function sendChatMessage({
  apiBaseUrl = DEFAULT_API_BASE_URL,
  apiFormat,
  endpointBaseUrl,
  apiKey,
  model,
  report,
  message,
  selectedIssueId = null,
  fetchImpl = fetch,
}) {
  const response = await requestJsonWithFallback({
    baseUrl: apiBaseUrl,
    path: '/review/chat',
    options: {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        api_format: apiFormat,
        base_url: endpointBaseUrl,
        api_key: apiKey,
        model,
        report,
        message,
        selected_issue_id: selectedIssueId,
      }),
    },
    fetchImpl,
  })

  return parseJsonResponse(response)
}
