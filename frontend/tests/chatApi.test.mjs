import test from 'node:test'
import assert from 'node:assert/strict'

import { sendChatMessage } from '../src/lib/chatApi.js'

test('sendChatMessage posts credentials and report instead of a process-local session id', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push({ url, options })
    return { ok: true, json: async () => ({ message: '好的，我来解释' }) }
  }
  const report = { total_score: 72, issues: [] }
  const result = await sendChatMessage({
    baseUrl: '/api',
    provider: 'openai',
    apiKey: 'user-key',
    model: 'gpt-5.2',
    report,
    message: '解释结论',
    selectedIssueId: 'HIGH-1',
    fetchImpl,
  })
  assert.equal(result.message, '好的，我来解释')
  assert.equal(calls[0].url, '/api/review/chat')
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    provider: 'openai',
    api_key: 'user-key',
    model: 'gpt-5.2',
    report,
    message: '解释结论',
    selected_issue_id: 'HIGH-1',
  })
})
test('sendChatMessage surfaces structured API errors and does not bypass the Vite proxy', async () => {
  const calls = []
  const fetchImpl = async (url) => {
    calls.push(url)
    return { ok: false, status: 400, json: async () => ({ detail: 'API Key 无效' }) }
  }
  await assert.rejects(() => sendChatMessage({
    baseUrl: '/api', provider: 'openai', apiKey: 'bad', model: 'gpt-5.2', report: {}, message: 'hi', fetchImpl,
  }), /API Key 无效/)
  assert.deepEqual(calls, ['/api/review/chat'])
})
