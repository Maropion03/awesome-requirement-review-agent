import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createApiUrl,
  mapReportToViewModel,
  startReviewStream,
  validateFormat,
} from '../src/lib/reviewApi.js'

test('createApiUrl joins base url and path without duplicate slashes', () => {
  assert.equal(createApiUrl('https://example.test/api/', '/review/run'), 'https://example.test/api/review/run')
})
test('validateFormat posts the user-owned endpoint and credentials', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push({ url, options })
    return { ok: true, json: async () => ({ status: 'ok', message: '连接成功' }) }
  }
  const result = await validateFormat({
    apiBaseUrl: '/api',
    apiFormat: 'anthropic_messages',
    endpointBaseUrl: 'https://api.example.com',
    apiKey: 'secret-key',
    model: 'claude-sonnet-5',
    fetchImpl,
  })
  assert.equal(result.status, 'ok')
  assert.equal(calls[0].url, '/api/formats/validate')
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    api_format: 'anthropic_messages',
    base_url: 'https://api.example.com',
    api_key: 'secret-key',
    model: 'claude-sonnet-5',
  })
})

test('startReviewStream consumes one NDJSON response without a server session', async () => {
  const encoder = new TextEncoder()
  const events = [
    { event: 'connected', api_format: 'openai_chat' },
    { event: 'dimension_start', dimension: '需求完整性' },
    { event: 'dimension_complete', dimension: '需求完整性', score: 8, status: 'completed' },
    { event: 'complete', report: { total_score: 80, recommendation: '通过', issues: [] } },
  ]
  const body = new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(events.map((event) => JSON.stringify(event)).join('\n') + '\n'))
      controller.close()
    },
  })
  const calls = []
  const received = []
  const fetchImpl = async (url, options) => {
    calls.push({ url, options })
    return { ok: true, body }
  }

  await startReviewStream({
    apiBaseUrl: '/api',
    file: new File(['# Demo\nA complete PRD body'], 'demo.md'),
    apiFormat: 'openai_chat',
    endpointBaseUrl: 'https://api.example.com/v1',
    apiKey: 'user-key',
    model: 'MiniMax-M2.7',
    preset: 'normal',
    fetchImpl,
    onConnected: (value) => received.push(value.event),
    onDimensionComplete: (value) => received.push(value.dimension),
    onComplete: (value) => received.push(value.total_score),
  })

  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, '/api/review/run')
  assert.ok(calls[0].options.body instanceof FormData)
  assert.equal(calls[0].options.body.get('api_key'), 'user-key')
  assert.equal(calls[0].options.body.get('api_format'), 'openai_chat')
  assert.equal(calls[0].options.body.get('base_url'), 'https://api.example.com/v1')
  assert.deepEqual(received, ['connected', '需求完整性', 80])
})

test('prepared PDFs send extracted text and diagram pages without raw PDF bytes', async () => {
  const body = new ReadableStream({ start(controller) { controller.close() } })
  let requestBody
  await startReviewStream({
    apiBaseUrl: '/api',
    file: new File(['raw-pdf-bytes'], 'demo.pdf'),
    preparedDocument: {
      documentText: 'Extracted PRD text with enough detail for review.',
      pageCount: 2,
      diagramPages: [{ pageNumber: 2, blob: new Blob(['jpeg-data'], { type: 'image/jpeg' }) }],
    },
    apiFormat: 'openai_chat', endpointBaseUrl: 'https://api.example.com/v1', apiKey: 'key', model: 'review-model', visionModel: 'vision-model', preset: 'normal',
    fetchImpl: async (url, options) => { requestBody = options.body; return { ok: true, body } },
  })
  assert.equal(requestBody.get('file'), null)
  assert.match(requestBody.get('document_text'), /Extracted PRD text/)
  assert.equal(requestBody.getAll('diagram_images').length, 1)
  assert.equal(requestBody.get('model'), 'review-model')
  assert.equal(requestBody.get('vision_model'), 'vision-model')
})

test('mapReportToViewModel preserves a 0-100 total and dimension evidence', () => {
  const viewModel = mapReportToViewModel({
    total_score: 76,
    recommendation: '修改后通过',
    summary: '综合评分 76/100，建议修改后通过',
    dimension_scores: [{ dimension: '需求完整性', score: 8.5, weight: 0.2, issues_count: 1, reasoning: '缺少异常场景' }],
    issues: [{ id: 'HIGH-1', display_id: 'HIGH-1', issue_key: 'issue::1', severity: 'HIGH', title: '验收标准缺失', dimension: '需求完整性', description: '只描述成功路径', suggestion: '补充异常场景', source_quote: '提交后显示成功', source_section: '验收标准', source_locator: '验收标准' }],
  })
  assert.equal(viewModel.score, '76')
  assert.equal(viewModel.suggestion, '修改后通过')
  assert.equal(viewModel.dimensionScores[0].topIssues[0].sourceQuote, '提交后显示成功')
  assert.equal(viewModel.rawReport.total_score, 76)
})
