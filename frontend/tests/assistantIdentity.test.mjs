import test from 'node:test'
import assert from 'node:assert/strict'

import {
  findIssueById,
  normalizeChatResponse,
} from '../src/lib/assistantPanel.js'
import { mapReportToViewModel } from '../src/lib/reviewApi.js'

test('findIssueById resolves display id and stable issue key', () => {
  const report = mapReportToViewModel({
    total_score: 6.8,
    recommendation: 'MODIFY',
    summary: 'demo',
    dimension_scores: [
      {
        dimension: '需求完整性',
        score: 6.5,
        weight: 0.2,
        issues_count: 1,
        reasoning: 'demo',
      },
    ],
    issues: [
      {
        id: 'HIGH-1',
        display_id: 'HIGH-1',
        issue_key: 'issue::abc123',
        severity: 'HIGH',
        title: '缺失功能交互流程的完整描述',
        dimension: '需求完整性',
        description: '未描述主流程与异常分支的交互路径',
        suggestion: '补充主流程、分支流程、异常状态和跳转关系',
      },
    ],
  })

  assert.equal(findIssueById(report, 'HIGH-1')?.issueKey, 'issue::abc123')
  assert.equal(findIssueById(report, 'issue::abc123')?.displayId, 'HIGH-1')
})

test('normalizeChatResponse preserves assistant status and selected issue', () => {
  const response = normalizeChatResponse({
    message: '模型回答：建议补齐主流程。',
    response_mode: 'model',
    assistant_status: 'model',
    selected_issue: {
      issue_key: 'issue::abc123',
      display_id: 'HIGH-1',
      title: '缺失功能交互流程的完整描述',
      dimension: '需求完整性',
      severity: 'HIGH',
    },
    suggested_actions: [{ type: 'generate_suggestion', label: '生成修改建议' }],
    source_refs: [],
    target_issue_id: 'HIGH-1',
    run_state: { status: 'completed' },
  })

  assert.equal(response.responseMode, 'model')
  assert.equal(response.assistantStatus, 'model')
  assert.equal(response.selectedIssue?.issueKey, 'issue::abc123')
  assert.equal(response.selectedIssue?.displayId, 'HIGH-1')
})
