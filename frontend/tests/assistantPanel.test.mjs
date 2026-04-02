import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildAssistantSnapshot,
  createAssistantState,
  normalizeChatResponse,
} from '../src/lib/assistantPanel.js'

test('createAssistantState initializes chat history and selected issue', () => {
  const state = createAssistantState()
  assert.deepEqual(state.chatMessages, [])
  assert.equal(state.selectedIssue, null)
})

test('buildAssistantSnapshot reflects report, run state, and issue context', () => {
  const snapshot = buildAssistantSnapshot({
    report: {
      score: '7.6',
      suggestion: '修改后通过',
      summary: '综合评分 7.6/10',
    },
    runState: {
      status: 'completed',
      progress: 100,
      current_dimension: '需求完整性',
    },
    selectedIssue: {
      id: '[高-1]',
      title: '验收标准缺失',
      description: '缺少失败场景',
    },
  })

  assert.equal(snapshot.score, '7.6')
  assert.equal(snapshot.status, 'completed')
  assert.equal(snapshot.currentDimension, '需求完整性')
  assert.equal(snapshot.selectedIssue.id, '[高-1]')
})

test('normalizeChatResponse keeps assistant payload stable', () => {
  const response = normalizeChatResponse({
    message: '好的，我来解释',
    suggested_actions: [{ type: 'rerun', label: '重新评审' }],
    source_refs: [{ type: 'issue', id: '[高-1]' }],
    target_issue_id: '[高-1]',
    run_state: { status: 'completed' },
  })

  assert.equal(response.message, '好的，我来解释')
  assert.equal(response.suggestedActions.length, 1)
  assert.equal(response.sourceRefs[0].id, '[高-1]')
  assert.equal(response.targetIssueId, '[高-1]')
  assert.equal(response.runState.status, 'completed')
})

test('normalizeChatResponse preserves retry action and assistant status', () => {
  const response = normalizeChatResponse({
    message: '模型暂时失败，请重试',
    response_mode: 'error',
    assistant_status: 'error',
    suggested_actions: [{ type: 'retry_chat', label: '重试回答' }],
    source_refs: [],
    target_issue_id: null,
    run_state: { status: 'completed' },
  })

  assert.equal(response.assistantStatus, 'error')
  assert.equal(response.responseMode, 'error')
  assert.equal(response.suggestedActions[0].type, 'retry_chat')
})
