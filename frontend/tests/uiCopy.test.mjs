import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function readSourceFile(relativePath) {
  return readFileSync(resolve(process.cwd(), relativePath), 'utf8')
}

test('primary workspace sections use plain titles without step numbering', () => {
  const uploadArea = readSourceFile('src/components/UploadArea.vue')
  const configPanel = readSourceFile('src/components/ConfigPanel.vue')
  const reviewProgress = readSourceFile('src/components/ReviewProgress.vue')
  const reportViewer = readSourceFile('src/components/ReportViewer.vue')

  assert.match(uploadArea, />上传 PRD 文档</)
  assert.doesNotMatch(uploadArea, /Step\s*1/i)

  assert.match(configPanel, />评审配置</)
  assert.doesNotMatch(configPanel, /Step\s*2/i)

  assert.match(reviewProgress, />评审进度</)
  assert.doesNotMatch(reviewProgress, /Step\s*3/i)

  assert.match(reportViewer, />评审报告</)
  assert.doesNotMatch(reportViewer, /Step\s*4/i)
})

test('app copy keeps plain titles and exposes a single chat entry button', () => {
  const app = readSourceFile('src/App.vue')

  assert.doesNotMatch(app, /Step\s*[1-5]/i)
  assert.doesNotMatch(app, /打开 Step 5/)
  assert.doesNotMatch(app, /返回 Step 4/)
  assert.doesNotMatch(app, /进入评审助手/)
  assert.doesNotMatch(app, /route-tabs/)
  assert.doesNotMatch(app, /操作提示/)
  assert.match(app, /进入对话/)
})

test('assistant page uses a back-to-report button instead of rerun trigger', () => {
  const app = readSourceFile('src/App.vue')

  assert.match(app, /goToRoute\(HASH_ROUTES\.report\)/)
  assert.match(app, />\s*返回报告\s*</)
})

test('assistant panel emphasizes conversation and composer visually', () => {
  const assistantPanel = readSourceFile('src/components/AssistantPanel.vue')

  assert.match(assistantPanel, /class="thread prominent"/)
  assert.match(assistantPanel, /class="composer composer-prominent"/)
})

test('assistant panel shows expand guidance for collapsible sections', () => {
  const assistantPanel = readSourceFile('src/components/AssistantPanel.vue')

  assert.match(assistantPanel, /class="summary-cue"/)
  assert.match(assistantPanel, /class="summary-arrow"/)
})

test('report viewer exposes evidence block for issue source references', () => {
  const reportViewer = readSourceFile('src/components/ReportViewer.vue')

  assert.match(reportViewer, /issue-evidence/)
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
