import test from 'node:test'
import assert from 'node:assert/strict'

import { sendChatMessage } from '../src/lib/chatApi.js'

test('sendChatMessage posts a chat payload and returns parsed response', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push({ url, options })
    return {
      ok: true,
      json: async () => ({
        message: '好的，我来解释',
        suggested_actions: [],
        source_refs: [],
        target_issue_id: null,
        run_state: {},
      }),
    }
  }

  const result = await sendChatMessage({
    baseUrl: 'http://127.0.0.1:8001/api',
    sessionId: 'session-1',
    message: '解释一下当前结论',
    selectedIssueId: '[高-1]',
    contextMode: 'default',
    fetchImpl,
  })

  assert.equal(result.message, '好的，我来解释')
  assert.equal(calls[0].url, 'http://127.0.0.1:8001/api/review/chat')
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    session_id: 'session-1',
    message: '解释一下当前结论',
    selected_issue_id: '[高-1]',
    context_mode: 'default',
  })
})

test('sendChatMessage retries the direct backend when the dev proxy returns 404', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push({ url, options })

    if (calls.length === 1) {
      return {
        ok: false,
        status: 404,
        headers: {
          get(name) {
            return name.toLowerCase() === 'content-type' ? 'text/html' : null
          },
        },
        json: async () => ({ detail: 'Not Found' }),
      }
    }

    return {
      ok: true,
      json: async () => ({
        message: '好的，我来解释',
        suggested_actions: [],
        source_refs: [],
        target_issue_id: null,
        run_state: {},
      }),
    }
  }

  const result = await sendChatMessage({
    baseUrl: '/api',
    sessionId: 'session-1',
    message: '解释一下当前结论',
    selectedIssueId: null,
    contextMode: 'default',
    fetchImpl,
  })

  assert.equal(result.message, '好的，我来解释')
  assert.equal(calls.length, 2)
  assert.equal(calls[0].url, '/api/review/chat')
  assert.equal(calls[1].url, 'http://127.0.0.1:8005/api/review/chat')
})

test('sendChatMessage keeps structured 404 responses instead of retrying direct backend', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push({ url, options })

    return {
      ok: false,
      status: 404,
      headers: {
        get(name) {
          return name.toLowerCase() === 'content-type' ? 'application/json' : null
        },
      },
      json: async () => ({ detail: 'Session not found' }),
    }
  }

  await assert.rejects(
    () =>
      sendChatMessage({
        baseUrl: '/api',
        sessionId: 'missing-session',
        message: '解释一下当前结论',
        selectedIssueId: null,
        contextMode: 'default',
        fetchImpl,
      }),
    /Session not found/,
  )

  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, '/api/review/chat')
})
