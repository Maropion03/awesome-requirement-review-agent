<template>
  <div class="app-shell">
    <SideBar
      :active-page="currentRoute"
      :run-status="runState.status"
      :preset="apiConfig.preset"
      :progress="runState.progress"
      :format-name="formatLabel"
      @navigate="goToRoute"
      @new-project="resetReviewRun"
    />

    <WorkbenchPage
      v-if="currentRoute === HASH_ROUTES.workbench"
      :selected-file-name="selectedFileName"
      :upload-state="uploadState"
      :upload-error="uploadError"
      :is-running="isRunning"
      :api-config="apiConfig"
      :product-context="productContext"
      :formats="formats"
      :stream-text="streamText"
      :agent-stages="agentStages"
      :dimensions="dimensions"
      :can-view-report="canViewReport"
      :can-open-assistant="canOpenAssistant"
      @update:selected-file-name="selectedFileName = $event"
      @update:api-config="updateApiConfig"
      @update:product-context="productContext = $event"
      @clear-product-context="clearStoredProductContext"
      @file-selected="handleFileSelected"
      @clear-file="clearSelectedFile"
      @start-review="startReviewFlow"
      @reset-demo="resetReviewRun"
      @navigate="goToRoute"
    />

    <ReportPage
      v-else-if="currentRoute === HASH_ROUTES.report"
      :report="report"
      :issue-state="issueState"
      :selected-issue-id="selectedIssueId"
      :can-open-assistant="canOpenAssistant"
      @issue-select="handleIssueSelection"
      @issue-status-change="handleIssueStatusChange"
      @export-suggestions="exportSuggestions"
      @open-assistant="goToRoute(HASH_ROUTES.assistant)"
      @rerun="goToRoute(HASH_ROUTES.workbench)"
      @navigate="goToRoute"
    />

    <AssistantPage
      v-else-if="currentRoute === HASH_ROUTES.assistant"
      :report="report"
      :can-chat="canOpenAssistant"
      :format-label="formatLabel"
      :chat-messages="chatMessages"
      :selected-issue="selectedIssue"
      :assistant-suggested-actions="assistantSuggestedActions"
      :assistant-source-refs="assistantSourceRefs"
      :assistant-status="assistantStatus"
      :assistant-response-mode="assistantResponseMode"
      :is-chat-loading="isChatLoading"
      :assistant-snapshot="assistantSnapshot"
      @send-message="submitChatMessage"
      @run-action="handleAssistantAction"
      @select-issue="handleIssueSelection"
      @back-to-report="goToRoute(HASH_ROUTES.report)"
      @export-suggestions="exportSuggestions"
      @rerun="goToRoute(HASH_ROUTES.workbench)"
      @navigate="goToRoute"
    />

    <SettingsPage
      v-else
      :api-config="apiConfig"
      :formats="formats"
      :can-view-report="canViewReport"
      :can-open-assistant="canOpenAssistant"
      @update:api-config="updateApiConfig"
      @clear-api-config="clearStoredApiConfig"
      @navigate="goToRoute"
    />

    <ModelCapabilityDialog
      :open="modelCapabilityDialogOpen"
      :review-model="apiConfig.model"
      :vision-model="effectiveVisionModel"
      @continue="resolveModelCapabilityDialog(true)"
      @configure="resolveModelCapabilityDialog(false)"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import SideBar from './components/layout/SideBar.vue'
import WorkbenchPage from './components/pages/WorkbenchPage.vue'
import ReportPage from './components/pages/ReportPage.vue'
import AssistantPage from './components/pages/AssistantPage.vue'
import SettingsPage from './components/pages/SettingsPage.vue'
import ModelCapabilityDialog from './components/ModelCapabilityDialog.vue'
import { clearApiConfig, loadApiConfig, resolveVisionModel, saveApiConfig } from './lib/apiConfigStorage.js'
import { createAgentStages, applyDimensionEvent, applyStreamingMessage, completeReporterStage } from './lib/agentStages.js'
import { buildAssistantSnapshot, createAssistantState, findIssueById, normalizeChatResponse } from './lib/assistantPanel.js'
import { sendChatMessage } from './lib/chatApi.js'
import { buildExportPayload } from './lib/exportSuggestions.js'
import { HASH_ROUTES, formatHashRoute, resolveHashRoute } from './lib/hashRoute.js'
import { buildIssueExportItems, getIssueIdentifier, mergeIssueStatuses, updateIssueStatus } from './lib/issueState.js'
import { shouldConfirmTextOnlyPdfReview } from './lib/modelCapabilities.js'
import {
  buildProductContextPayload,
  clearProductContext,
  createEmptyProductContext,
  loadProductContext,
  saveProductContext,
} from './lib/productContextStorage.js'
import {
  API_FORMAT_FALLBACKS,
  createBaseDimensions,
  createEmptyReportViewModel,
  loadFormatCatalog,
  mapReportToViewModel,
  startReviewStream,
} from './lib/reviewApi.js'

const MAX_FILE_BYTES = 3_500_000

function createRunState() {
  return { status: 'idle', progress: 0, current_dimension: null, completed_dimensions: [] }
}

function getWindowHash() {
  return typeof window === 'undefined' ? '' : window.location.hash
}

const currentRoute = ref(resolveHashRoute({ hash: getWindowHash(), fallback: HASH_ROUTES.workbench }))
const formats = ref(API_FORMAT_FALLBACKS)
const defaultApiConfig = {
  apiFormat: API_FORMAT_FALLBACKS[0].id,
  baseUrl: API_FORMAT_FALLBACKS[0].default_base_url,
  apiKey: '',
  model: API_FORMAT_FALLBACKS[0].default_model,
  visionModel: '',
  preset: 'normal',
}
const browserStorage = typeof window !== 'undefined' ? window.localStorage : null
const apiConfig = ref(loadApiConfig({ storage: browserStorage, fallback: defaultApiConfig }))
const productContext = ref(loadProductContext({ storage: browserStorage }))
const selectedFile = ref(null)
const selectedFileName = ref('')
const uploadState = ref('idle')
const uploadError = ref('')
const isRunning = ref(false)
const streamText = ref('')
const agentStages = ref(createAgentStages())
const dimensions = ref(createBaseDimensions())
const report = ref(createEmptyReportViewModel())
const issueState = ref({})
const selectedIssue = ref(null)
const runState = ref(createRunState())
const chatMessages = ref([])
const assistantSuggestedActions = ref([])
const assistantSourceRefs = ref([])
const assistantStatus = ref('unavailable')
const assistantResponseMode = ref('report_level')
const isChatLoading = ref(false)
const modelCapabilityDialogOpen = ref(false)
let reviewController = null
let modelCapabilityDialogResolver = null

const canViewReport = computed(() => Boolean(report.value.rawReport))
const canOpenAssistant = computed(() => Boolean(
  report.value.rawReport && apiConfig.value.apiKey.trim() && apiConfig.value.model.trim() && apiConfig.value.baseUrl.trim(),
))
const formatLabel = computed(() => {
  const format = formats.value.find((item) => item.id === apiConfig.value.apiFormat)
  return `${format?.name || apiConfig.value.apiFormat} · ${apiConfig.value.model}`
})
const effectiveVisionModel = computed(() => resolveVisionModel(apiConfig.value))
const selectedIssueId = computed(() => getIssueIdentifier(selectedIssue.value) || '')
const assistantSnapshot = computed(() => buildAssistantSnapshot({ report: report.value, runState: runState.value, selectedIssue: selectedIssue.value }))

function normalizeAccessibleRoute(route) {
  if (route === HASH_ROUTES.settings) return route
  if (route === HASH_ROUTES.assistant && !canOpenAssistant.value) return canViewReport.value ? HASH_ROUTES.report : HASH_ROUTES.workbench
  if (route === HASH_ROUTES.report && !canViewReport.value) return HASH_ROUTES.workbench
  return route
}

function syncRouteFromHash() {
  const requested = resolveHashRoute({ hash: getWindowHash(), fallback: HASH_ROUTES.workbench })
  const next = normalizeAccessibleRoute(requested)
  currentRoute.value = next
  if (typeof window !== 'undefined' && requested !== next) window.location.hash = formatHashRoute(next)
}

function goToRoute(route) {
  const next = normalizeAccessibleRoute(route)
  currentRoute.value = next
  if (typeof window !== 'undefined' && window.location.hash !== formatHashRoute(next)) window.location.hash = formatHashRoute(next)
}

function resetAssistantState() {
  const initial = createAssistantState()
  chatMessages.value = [...initial.chatMessages]
  assistantSuggestedActions.value = [...initial.suggestedActions]
  assistantSourceRefs.value = [...initial.sourceRefs]
  assistantStatus.value = initial.assistantStatus
  assistantResponseMode.value = initial.responseMode
  isChatLoading.value = false
}

function cancelReview() {
  reviewController?.abort()
  reviewController = null
}

function resetReviewRun() {
  cancelReview()
  isRunning.value = false
  streamText.value = ''
  agentStages.value = createAgentStages()
  dimensions.value = createBaseDimensions()
  report.value = createEmptyReportViewModel()
  issueState.value = {}
  selectedIssue.value = null
  runState.value = createRunState()
  uploadState.value = selectedFile.value ? 'ready' : 'idle'
  uploadError.value = ''
  resetAssistantState()
  goToRoute(HASH_ROUTES.workbench)
}

function updateApiConfig(next) {
  apiConfig.value = { ...apiConfig.value, ...next }
}

function clearStoredApiConfig() {
  clearApiConfig({ storage: browserStorage })
  apiConfig.value = { ...defaultApiConfig }
}

function clearStoredProductContext() {
  clearProductContext({ storage: browserStorage })
  productContext.value = createEmptyProductContext()
}

function appendStreamLine(line) {
  if (line) streamText.value = streamText.value ? `${streamText.value}\n${line}` : line
}

function requestModelCapabilityConfirmation() {
  modelCapabilityDialogOpen.value = true
  return new Promise((resolve) => { modelCapabilityDialogResolver = resolve })
}

function resolveModelCapabilityDialog(shouldContinue) {
  modelCapabilityDialogOpen.value = false
  modelCapabilityDialogResolver?.(shouldContinue)
  modelCapabilityDialogResolver = null
  if (!shouldContinue) goToRoute(HASH_ROUTES.settings)
}

function markDimensionStatus(dimensionName, status) {
  dimensions.value = dimensions.value.map((item) => item.name === dimensionName ? { ...item, status } : item)
}

function validateFile(file) {
  if (!file) return '请选择一份 PRD 文档'
  if (!/\.(md|docx|pdf)$/i.test(file.name)) return '仅支持 .md、.docx 和 .pdf 文档'
  if (file.size > MAX_FILE_BYTES) return '文档不能超过 3.5MB'
  return ''
}

function handleFileSelected(file) {
  const error = validateFile(file)
  if (error) {
    selectedFile.value = null
    selectedFileName.value = ''
    uploadState.value = 'error'
    uploadError.value = error
    return
  }
  resetReviewRun()
  selectedFile.value = file
  selectedFileName.value = file.name
  uploadState.value = 'ready'
  uploadError.value = ''
}

function clearSelectedFile() {
  resetReviewRun()
  selectedFile.value = null
  selectedFileName.value = ''
  uploadState.value = 'idle'
}

async function startReviewFlow() {
  if (isRunning.value || modelCapabilityDialogOpen.value) return
  const fileError = validateFile(selectedFile.value)
  if (fileError) {
    uploadState.value = 'error'
    uploadError.value = fileError
    return
  }
  if (!apiConfig.value.apiKey.trim() || !apiConfig.value.model.trim() || !apiConfig.value.baseUrl.trim()) {
    uploadError.value = '请先填写接口格式、Base URL、API Key 和模型名'
    return
  }
  if (shouldConfirmTextOnlyPdfReview({ fileName: selectedFile.value.name, model: apiConfig.value.model })) {
    const shouldContinue = await requestModelCapabilityConfirmation()
    if (!shouldContinue) return
  }

  cancelReview()
  streamText.value = ''
  agentStages.value = createAgentStages()
  dimensions.value = createBaseDimensions()
  report.value = createEmptyReportViewModel()
  issueState.value = {}
  selectedIssue.value = null
  resetAssistantState()
  isRunning.value = true
  uploadState.value = 'uploading'
  uploadError.value = ''
  runState.value = { ...createRunState(), status: 'reviewing' }
  reviewController = new AbortController()

  try {
    const contextPayload = buildProductContextPayload(productContext.value)
    let preparedDocument = null
    if (/\.pdf$/i.test(selectedFile.value.name)) {
      appendStreamLine('正在浏览器本地提取 PDF 文本并定位流程图候选页面…')
      const { preparePdfForReview } = await import('./lib/pdfClientParser.js')
      preparedDocument = await preparePdfForReview(selectedFile.value)
      appendStreamLine(`PDF 已提取 ${preparedDocument.pageCount} 页，发现 ${preparedDocument.diagramPages.length} 个视觉候选页面。`)
      if (preparedDocument.diagramPages.length && effectiveVisionModel.value !== apiConfig.value.model.trim()) {
        appendStreamLine(`流程图将由视觉模型 ${effectiveVisionModel.value} 识别；正文继续使用 ${apiConfig.value.model.trim()}。`)
      }
    }
    await startReviewStream({
      file: selectedFile.value,
      preparedDocument,
      apiFormat: apiConfig.value.apiFormat,
      endpointBaseUrl: apiConfig.value.baseUrl,
      apiKey: apiConfig.value.apiKey,
      model: apiConfig.value.model,
      visionModel: effectiveVisionModel.value,
      productContext: contextPayload,
      preset: apiConfig.value.preset,
      signal: reviewController.signal,
      onConnected: () => appendStreamLine(`已连接 ${formatLabel.value}`),
      onDimensionStart: (payload) => {
        markDimensionStatus(payload.dimension, 'active')
        agentStages.value = applyDimensionEvent(agentStages.value, 'start', payload.dimension)
        runState.value = { ...runState.value, current_dimension: payload.dimension }
      },
      onDimensionComplete: (payload) => {
        markDimensionStatus(payload.dimension, payload.status === 'degraded' ? 'error' : 'complete')
        agentStages.value = applyDimensionEvent(agentStages.value, 'complete', payload.dimension)
        const completed = Array.from(new Set([...runState.value.completed_dimensions, payload.dimension]))
        runState.value = { ...runState.value, completed_dimensions: completed, progress: Math.round((completed.length / dimensions.value.length) * 100) }
        appendStreamLine(`${payload.dimension}：${payload.status === 'degraded' ? `降级（${payload.message}）` : `${payload.score}/10`}`)
      },
      onStreaming: (payload) => {
        appendStreamLine(payload.content)
        agentStages.value = applyStreamingMessage(agentStages.value, payload.content || '')
      },
      onComplete: (payload) => {
        report.value = mapReportToViewModel(payload)
        issueState.value = mergeIssueStatuses({}, report.value.issues)
      },
      onError: (payload) => appendStreamLine(payload.message || '评审失败'),
    })

    if (!report.value.rawReport) throw new Error('评审流结束但没有生成报告')
    isRunning.value = false
    uploadState.value = 'uploaded'
    runState.value = { ...runState.value, status: 'completed', progress: 100, current_dimension: null }
    agentStages.value = completeReporterStage(agentStages.value)
    assistantStatus.value = 'model'
    assistantResponseMode.value = 'model'
    goToRoute(HASH_ROUTES.report)
  } catch (error) {
    if (error?.name === 'AbortError') return
    isRunning.value = false
    uploadState.value = 'error'
    uploadError.value = error instanceof Error ? error.message : '评审失败，请稍后重试'
    runState.value = { ...runState.value, status: 'error' }
  } finally {
    reviewController = null
  }
}

function handleIssueSelection(issueOrId) {
  const next = typeof issueOrId === 'string' ? findIssueById(report.value, issueOrId) : issueOrId
  if (!next) return
  selectedIssue.value = next
  if (currentRoute.value === HASH_ROUTES.report && canOpenAssistant.value) goToRoute(HASH_ROUTES.assistant)
}

function handleIssueStatusChange(payload) {
  const issueId = payload?.issueId || getIssueIdentifier(payload?.issue)
  if (issueId) issueState.value = updateIssueStatus(issueState.value, issueId, payload.status)
}

function exportSuggestions() {
  const exportPayload = buildExportPayload({ fileName: 'prd-review-suggestions.md', issues: buildIssueExportItems(report.value.issues, issueState.value) })
  if (typeof document === 'undefined') return
  const url = URL.createObjectURL(new Blob([exportPayload.content], { type: exportPayload.mimeType }))
  const link = document.createElement('a')
  link.href = url
  link.download = exportPayload.fileName
  link.click()
  URL.revokeObjectURL(url)
}

function addChatMessage(role, content, extra = {}) {
  chatMessages.value = [...chatMessages.value, { role, content, timestamp: new Date().toISOString(), ...extra }]
}

async function submitChatMessage(message) {
  const content = String(message || '').trim()
  if (!content || !canOpenAssistant.value) return
  addChatMessage('user', content)
  isChatLoading.value = true
  try {
    const normalized = normalizeChatResponse(await sendChatMessage({
      apiFormat: apiConfig.value.apiFormat,
      endpointBaseUrl: apiConfig.value.baseUrl,
      apiKey: apiConfig.value.apiKey,
      model: apiConfig.value.model,
      report: report.value.rawReport,
      message: content,
      selectedIssueId: selectedIssueId.value || null,
    }))
    assistantSuggestedActions.value = normalized.suggestedActions
    assistantSourceRefs.value = normalized.sourceRefs
    assistantStatus.value = normalized.assistantStatus
    assistantResponseMode.value = normalized.responseMode
    const target = findIssueById(report.value, normalized.targetIssueId)
    if (target) selectedIssue.value = target
    addChatMessage('assistant', normalized.message || '助手未返回可展示的内容。', { sourceRefs: normalized.sourceRefs })
  } catch (error) {
    assistantStatus.value = 'error'
    assistantResponseMode.value = 'error'
    addChatMessage('system', error instanceof Error ? error.message : '对话失败，请稍后重试')
  } finally {
    isChatLoading.value = false
  }
}

async function handleAssistantAction(action) {
  if (!action) return
  if (action.type === 'rerun') { goToRoute(HASH_ROUTES.workbench); return }
  if (action.type === 'focus_issue' && action.issue_id) { handleIssueSelection(action.issue_id); return }
  if (action.type === 'retry_chat') {
    const last = [...chatMessages.value].reverse().find((item) => item.role === 'user')
    if (last) await submitChatMessage(last.content)
    return
  }
  if (action.type === 'switch_preset' && action.preset) { updateApiConfig({ preset: action.preset }); goToRoute(HASH_ROUTES.workbench); return }
  await submitChatMessage(action.type === 'generate_suggestion' ? '给我修改建议' : action.label)
}

watch(() => report.value.issues, (issues) => {
  issueState.value = mergeIssueStatuses(issueState.value, issues || [])
  if (selectedIssue.value) selectedIssue.value = findIssueById(report.value, selectedIssueId.value)
}, { deep: true })

watch(apiConfig, (next) => {
  saveApiConfig(next, { storage: browserStorage })
}, { deep: true })

watch(productContext, (next) => {
  saveProductContext(next, { storage: browserStorage })
}, { deep: true })

onMounted(async () => {
  if (typeof window !== 'undefined') {
    syncRouteFromHash()
    window.addEventListener('hashchange', syncRouteFromHash)
  }
  try {
    const catalog = await loadFormatCatalog()
    if (Array.isArray(catalog.formats) && catalog.formats.length) formats.value = catalog.formats
  } catch {
    // Built-in catalog keeps the UI usable when the API is starting up.
  }
})

onBeforeUnmount(() => {
  cancelReview()
  modelCapabilityDialogResolver?.(false)
  if (typeof window !== 'undefined') window.removeEventListener('hashchange', syncRouteFromHash)
})
</script>

<style scoped>
.app-shell { min-height: 100vh; }
</style>
