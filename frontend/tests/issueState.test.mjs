import test from 'node:test'
import assert from 'node:assert/strict'

import {
  DEFAULT_STATE,
  SUPPORTED_STATUSES,
  createIssueState,
  getIssueIdentifier,
  getIssueStatus,
  normalizeStatus,
  updateIssueStatus,
  mergeIssueStatuses,
  buildIssueExportItems,
} from '../src/lib/issueState.js'
import { buildSuggestionExport, buildExportPayload } from '../src/lib/exportSuggestions.js'

test('createIssueState builds a local state map from issue identifiers', () => {
  const state = createIssueState([
    { issueKey: 'issue::a', displayId: 'HIGH-1' },
    { displayId: 'MEDIUM-1' },
    { id: 'LOW-1' },
  ])

  assert.deepEqual(Object.keys(state), ['issue::a', 'MEDIUM-1', 'LOW-1'])
  assert.equal(state['issue::a'].status, DEFAULT_STATE)
  assert.equal(state['MEDIUM-1'].status, DEFAULT_STATE)
  assert.equal(state['LOW-1'].status, DEFAULT_STATE)
})

test('updateIssueStatus stores the next status by issue key', () => {
  const state = createIssueState([{ issueKey: 'issue::a', displayId: 'HIGH-1' }])
  const next = updateIssueStatus(state, 'issue::a', 'accepted')

  assert.equal(next['issue::a'].status, 'accepted')
  assert.equal(getIssueStatus(next, { issueKey: 'issue::a' }), 'accepted')
})

test('normalizeStatus falls back for unsupported values', () => {
  assert.equal(normalizeStatus('accepted'), 'accepted')
  assert.equal(normalizeStatus('unknown'), DEFAULT_STATE)
  assert.deepEqual(
    SUPPORTED_STATUSES,
    ['todo', 'accepted', 'ignored', 'fixed_pending_verify'],
  )
})

test('mergeIssueStatuses preserves existing state and updates changed issues only', () => {
  const current = {
    'issue::a': { status: 'accepted' },
    'issue::b': { status: 'ignored' },
  }

  const next = mergeIssueStatuses(current, [
    { issueKey: 'issue::a', displayId: 'HIGH-1' },
    { issueKey: 'issue::c', displayId: 'HIGH-2' },
  ])

  assert.equal(next['issue::a'].status, 'accepted')
  assert.equal(next['issue::c'].status, DEFAULT_STATE)
  assert.equal(next['issue::b'], undefined)
})

test('buildIssueExportItems attaches local status to issues', () => {
  const state = {
    'issue::a': { status: 'accepted' },
    'HIGH-2': { status: 'ignored' },
  }

  const items = buildIssueExportItems(
    [
      { issueKey: 'issue::a', displayId: 'HIGH-1', title: 'A', description: 'desc A', suggestion: 'fix A' },
      { displayId: 'HIGH-2', title: 'B', description: 'desc B', suggestion: 'fix B' },
    ],
    state,
  )

  assert.equal(items[0].status, 'accepted')
  assert.equal(items[1].status, 'ignored')
})

test('buildSuggestionExport only includes accepted or pending-fix issues', () => {
  const markdown = buildSuggestionExport({
    issues: [
      { displayId: 'HIGH-1', title: '验收标准缺失', suggestion: '补充失败重试', description: '只描述成功路径', status: 'accepted' },
      { displayId: 'LOW-1', title: '术语不统一', suggestion: '统一术语', description: '多处术语混用', status: 'ignored' },
      { displayId: 'MEDIUM-1', title: '边界场景不足', suggestion: '补充失败场景', description: '缺少失败处理', status: 'fixed_pending_verify' },
    ],
  })

  assert.match(markdown, /HIGH-1/)
  assert.match(markdown, /MEDIUM-1/)
  assert.doesNotMatch(markdown, /LOW-1/)
})

test('buildExportPayload returns a markdown download contract', () => {
  const payload = buildExportPayload({
    fileName: 'prd-review-suggestions.md',
    issues: [
      { displayId: 'HIGH-1', title: '验收标准缺失', suggestion: '补充失败重试', description: '只描述成功路径', status: 'accepted' },
    ],
  })

  assert.equal(payload.fileName, 'prd-review-suggestions.md')
  assert.equal(payload.mimeType, 'text/markdown;charset=utf-8')
  assert.match(payload.content, /HIGH-1/)
})

test('getIssueIdentifier uses issueKey, then displayId, then id', () => {
  assert.equal(getIssueIdentifier({ issueKey: 'issue::a', displayId: 'HIGH-1', id: '1' }), 'issue::a')
  assert.equal(getIssueIdentifier({ displayId: 'HIGH-1', id: '1' }), 'HIGH-1')
  assert.equal(getIssueIdentifier({ id: '1' }), '1')
  assert.equal(getIssueIdentifier(null), null)
})
