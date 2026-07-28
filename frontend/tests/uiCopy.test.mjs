import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function readSourceFile(relativePath) {
  return readFileSync(resolve(process.cwd(), relativePath), 'utf8')
}

test('primary workspace exposes document, BYOK configuration, progress, and report', () => {
  const uploadArea = readSourceFile('src/components/UploadArea.vue')
  const configPanel = readSourceFile('src/components/ConfigPanel.vue')
  const reviewProgress = readSourceFile('src/components/ReviewProgress.vue')
  const reportViewer = readSourceFile('src/components/ReportViewer.vue')

  assert.match(uploadArea, />上传 PRD 文档</)
  assert.match(uploadArea, /3\.5MB/)

  assert.match(configPanel, />连接你的模型</)
  assert.match(configPanel, /API Key/)
  assert.match(configPanel, /localStorage/)

  assert.match(reviewProgress, />评审进度</)
  assert.match(reportViewer, /结论摘要/)
  assert.match(reportViewer, /详细问题/)
})

test('app copy keeps plain titles and exposes a single chat entry button', () => {
  const app = readSourceFile('src/App.vue')
  const reportPage = readSourceFile('src/components/pages/ReportPage.vue')

  assert.doesNotMatch(app, /sessionId|EventSource|localStorage/)
  assert.match(reportPage, /进入助手/)
  assert.equal((reportPage.match(/进入助手/g) || []).length, 1)
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

test('assistant page restores the formal workflow context rail', () => {
  const assistantPage = readSourceFile('src/components/pages/AssistantPage.vue')

  assert.match(assistantPage, /class="context-rail"/)
  assert.match(assistantPage, /Workflow/)
  assert.match(assistantPage, /Selected issue/)
  assert.match(assistantPage, /Issue shortcuts/)
  assert.doesNotMatch(assistantPage, /class="assistant-summary-grid"/)
})

test('report viewer exposes evidence block for issue source references', () => {
  const reportViewer = readSourceFile('src/components/ReportViewer.vue')

  assert.match(reportViewer, /evidence-quote/)
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
