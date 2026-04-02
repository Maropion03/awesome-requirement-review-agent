import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createApiUrl,
  uploadPrd,
  startReview,
  createReviewStream,
  mapReportToViewModel,
} from '../src/lib/reviewApi.js'

test('createApiUrl joins base url and path without duplicate slashes', () => {
  assert.equal(
    createApiUrl('http://127.0.0.1:8001/api/', '/review/upload'),
    'http://127.0.0.1:8001/api/review/upload',
  )
})

test('uploadPrd posts multipart form data and returns parsed response', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push({ url, options })
    return {
      ok: true,
      json: async () => ({
        session_id: 'session-1',
        filename: 'demo.md',
        file_type: 'markdown',
        size: 10,
      }),
    }
  }

  const file = new File(['# PRD'], 'demo.md', { type: 'text/markdown' })
  const result = await uploadPrd({
    baseUrl: 'http://127.0.0.1:8001/api',
    file,
    fetchImpl,
  })

  assert.equal(result.session_id, 'session-1')
  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, 'http://127.0.0.1:8001/api/review/upload')
  assert.equal(calls[0].options.method, 'POST')
  assert.ok(calls[0].options.body instanceof FormData)
})

test('startReview posts session id and preset', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push({ url, options })
    return {
      ok: true,
      json: async () => ({ status: 'started', session_id: 'session-1' }),
    }
  }

  const result = await startReview({
    baseUrl: 'http://127.0.0.1:8001/api',
    sessionId: 'session-1',
    preset: 'innovation',
    fetchImpl,
  })

  assert.equal(result.status, 'started')
  assert.equal(calls[0].url, 'http://127.0.0.1:8001/api/review/start')
  assert.equal(calls[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    session_id: 'session-1',
    preset: 'innovation',
  })
})

test('mapReportToViewModel adapts backend report for current viewer', () => {
  const viewModel = mapReportToViewModel({
    total_score: 7.6,
    recommendation: 'MODIFY',
    summary: '综合评分 7.6/10，建议修改后通过',
    dimension_scores: [
      {
        dimension: '需求完整性',
        score: 8.5,
        weight: 0.2,
        issues_count: 2,
        reasoning: '缺少异常场景',
      },
    ],
    issues: [
      {
        id: 'H-1',
        display_id: 'H-1',
        issue_key: 'issue::evidence-1',
        severity: 'HIGH',
        title: '验收标准缺失',
        dimension: '需求完整性',
        description: '只描述成功路径',
        suggestion: '补充失败和异常场景',
        source_quote: '验收标准：用户提交后显示成功',
        source_section: '验收标准',
        source_locator: 'line:18',
      },
      {
        id: 'M-1',
        display_id: 'M-1',
        issue_key: 'issue::evidence-2',
        severity: 'MEDIUM',
        title: '优先级说明不清',
        dimension: '优先级一致性',
        description: '优先级依据缺失',
      },
    ],
  })

  assert.equal(viewModel.score, '7.6')
  assert.equal(viewModel.suggestion, '修改后通过')
  assert.equal(viewModel.summary, '综合评分 7.6/10，建议修改后通过')
  assert.deepEqual(viewModel.dimensionScores, [
      {
        dimension: '需求完整性',
        score: '8.5',
        weightLabel: '20%',
        issuesCount: 2,
        highIssuesCount: 1,
        statusLabel: '需重点关注',
        statusTone: 'danger',
        summary: '验收标准缺失',
        actionHints: ['补充失败和异常场景'],
        topIssues: [
          {
            id: 'H-1',
            displayId: 'H-1',
            issueKey: 'issue::evidence-1',
            level: '高',
            severity: 'HIGH',
            title: '验收标准缺失',
            dimension: '需求完整性',
            description: '只描述成功路径',
            suggestion: '补充失败和异常场景',
            sourceQuote: '验收标准：用户提交后显示成功',
            sourceSection: '验收标准',
            sourceLocator: 'line:18',
          },
        ],
        reasoning: '缺少异常场景',
      },
  ])
  assert.deepEqual(viewModel.issueGroups, [
    {
      severity: 'HIGH',
      label: '高优先级',
      count: 1,
      issues: [
        {
          id: 'H-1',
          displayId: 'H-1',
          issueKey: 'issue::evidence-1',
          level: '高',
          severity: 'HIGH',
          title: '验收标准缺失',
          dimension: '需求完整性',
          description: '只描述成功路径',
          suggestion: '补充失败和异常场景',
          sourceQuote: '验收标准：用户提交后显示成功',
          sourceSection: '验收标准',
          sourceLocator: 'line:18',
        },
      ],
    },
    {
      severity: 'MEDIUM',
      label: '中优先级',
      count: 1,
      issues: [
        {
          id: 'M-1',
          displayId: 'M-1',
          issueKey: 'issue::evidence-2',
          level: '中',
          severity: 'MEDIUM',
          title: '优先级说明不清',
          dimension: '优先级一致性',
          description: '优先级依据缺失',
          suggestion: '未提供修改建议',
          sourceQuote: '',
          sourceSection: '',
          sourceLocator: '',
        },
      ],
    },
  ])
  assert.equal(viewModel.rawReport.total_score, 7.6)
})

test('createReviewStream marks transport errors as recoverable while reconnecting', () => {
  class FakeEventSource {
    static CONNECTING = 0
    static OPEN = 1
    static CLOSED = 2
    static instances = []

    constructor(url) {
      this.url = url
      this.readyState = FakeEventSource.OPEN
      this.handlers = new Map()
      FakeEventSource.instances.push(this)
    }

    addEventListener(eventName, handler) {
      this.handlers.set(eventName, handler)
    }

    close() {
      this.readyState = FakeEventSource.CLOSED
    }
  }

  const errors = []
  createReviewStream({
    baseUrl: '/api',
    sessionId: 'session-1',
    EventSourceImpl: FakeEventSource,
    onError(data) {
      errors.push(data)
    },
  })

  const stream = FakeEventSource.instances[0]
  stream.readyState = FakeEventSource.CONNECTING
  stream.handlers.get('error')({})

  assert.equal(errors.length, 1)
  assert.deepEqual(errors[0], {
    message: '评审连接中断，正在重连',
    recoverable: true,
  })
})

test('createReviewStream keeps backend error payload as non-recoverable', () => {
  class FakeEventSource {
    static CONNECTING = 0
    static OPEN = 1
    static CLOSED = 2
    static instances = []

    constructor(url) {
      this.url = url
      this.readyState = FakeEventSource.OPEN
      this.handlers = new Map()
      FakeEventSource.instances.push(this)
    }

    addEventListener(eventName, handler) {
      this.handlers.set(eventName, handler)
    }

    close() {
      this.readyState = FakeEventSource.CLOSED
    }
  }

  const errors = []
  createReviewStream({
    baseUrl: '/api',
    sessionId: 'session-1',
    EventSourceImpl: FakeEventSource,
    onError(data) {
      errors.push(data)
    },
  })

  const stream = FakeEventSource.instances[0]
  stream.handlers.get('error')({
    data: JSON.stringify({ message: '后端评审失败' }),
  })

  assert.equal(errors.length, 1)
  assert.deepEqual(errors[0], {
    message: '后端评审失败',
    recoverable: false,
  })
})

test('createReviewStream forwards complete payloads emitted directly by the backend', () => {
  class FakeEventSource {
    static CONNECTING = 0
    static OPEN = 1
    static CLOSED = 2
    static instances = []

    constructor(url) {
      this.url = url
      this.readyState = FakeEventSource.OPEN
      this.handlers = new Map()
      FakeEventSource.instances.push(this)
    }

    addEventListener(eventName, handler) {
      this.handlers.set(eventName, handler)
    }

    close() {
      this.readyState = FakeEventSource.CLOSED
    }
  }

  const reports = []
  createReviewStream({
    baseUrl: '/api',
    sessionId: 'session-1',
    EventSourceImpl: FakeEventSource,
    onComplete(report) {
      reports.push(report)
    },
  })

  const stream = FakeEventSource.instances[0]
  stream.handlers.get('complete')({
    data: JSON.stringify({
      total_score: 7.8,
      recommendation: 'MODIFY',
      summary: '综合评分 7.8/10',
    }),
  })

  assert.equal(reports.length, 1)
  assert.deepEqual(reports[0], {
    total_score: 7.8,
    recommendation: 'MODIFY',
    summary: '综合评分 7.8/10',
  })
})
