import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function readSourceFile(relativePath) {
  return readFileSync(resolve(process.cwd(), relativePath), 'utf8')
}

test('primary workspace exposes document, persisted BYOK settings, progress, and report', () => {
  const uploadArea = readSourceFile('src/components/UploadArea.vue')
  const configPanel = readSourceFile('src/components/ConfigPanel.vue')
  const reviewProgress = readSourceFile('src/components/ReviewProgress.vue')
  const reportViewer = readSourceFile('src/components/ReportViewer.vue')

  assert.match(uploadArea, /拖拽 PRD 到这里/)
  assert.match(uploadArea, /3\.5MB/)

  assert.match(configPanel, />连接你的模型</)
  assert.match(configPanel, /API Key/)
  assert.match(configPanel, /localStorage/)

  assert.match(reviewProgress, />实时进度</)
  assert.match(reportViewer, /Recommendation/)
  assert.match(reportViewer, /详细问题/)
})

test('app exposes one assistant entry and persisted browser configuration', () => {
  const app = readSourceFile('src/App.vue')
  const reportPage = readSourceFile('src/components/pages/ReportPage.vue')

  assert.doesNotMatch(app, /sessionId|EventSource/)
  assert.match(app, /loadApiConfig/)
  assert.match(app, /saveApiConfig/)
  assert.match(reportPage, /打开助手/)
  assert.equal((reportPage.match(/打开助手/g) || []).length, 1)
})

test('assistant page uses a back-to-report button instead of rerun trigger', () => {
  const app = readSourceFile('src/App.vue')
  const assistantPage = readSourceFile('src/components/pages/AssistantPage.vue')

  assert.match(app, /goToRoute\(HASH_ROUTES\.report\)/)
  assert.match(assistantPage, /back-to-report/)
  assert.match(assistantPage, /返回报告/)
})

test('assistant panel emphasizes conversation and composer visually', () => {
  const assistantPanel = readSourceFile('src/components/AssistantPanel.vue')

  assert.match(assistantPanel, /class="message-list"/)
  assert.match(assistantPanel, /class="composer"/)
  assert.match(assistantPanel, /typing-indicator/)
  assert.match(assistantPanel, /starter-prompts/)
  assert.match(assistantPanel, /\$emit\('open-report'\)/)
})

test('assistant page restores the original report context rail', () => {
  const assistantPage = readSourceFile('src/components/pages/AssistantPage.vue')

  assert.match(assistantPage, /class="context-rail"/)
  assert.match(assistantPage, /Run summary/)
  assert.match(assistantPage, /Report summary/)
  assert.match(assistantPage, /Issue shortcuts/)
  assert.doesNotMatch(assistantPage, /class="assistant-summary-grid"/)
})

test('report viewer exposes evidence block for issue source references', () => {
  const reportViewer = readSourceFile('src/components/ReportViewer.vue')

  assert.match(reportViewer, /原文依据/)
  assert.match(reportViewer, /sourceQuote|sourceSection|sourceLocator/)
})

test('report viewer exposes local issue status controls and export trigger', () => {
  const reportViewer = readSourceFile('src/components/ReportViewer.vue')

  assert.match(reportViewer, /待处理/)
  assert.match(reportViewer, /已采纳/)
  assert.match(reportViewer, /已忽略/)
  assert.match(reportViewer, /待复核/)
  assert.match(reportViewer, /导出修改建议/)
})
