<template>
  <div class="app-shell">
    <TopNavigation :current-project="currentProject" user-name="Ann" user-initials="AN" />
    <SideBar :active-page="currentRoute" @navigate="goToRoute" />

    <div v-if="currentRoute === HASH_ROUTES.report" class="route-actions">
      <button
        class="route-button primary"
        type="button"
        :disabled="!canOpenAssistant"
        @click="goToRoute(HASH_ROUTES.assistant)"
      >
        进入对话
      </button>
    </div>

    <div v-if="currentRoute === HASH_ROUTES.assistant" class="route-actions">
      <button class="route-button" type="button" @click="goToRoute(HASH_ROUTES.report)">
        返回报告
      </button>
    </div>

    <WorkbenchPage
      v-if="currentRoute === HASH_ROUTES.workbench"
      :selected-file-name="selectedFileName"
      :upload-state="uploadState"
      :upload-error="uploadError"
      :is-running="isRunning"
      :preset="preset"
      :stream-text="streamText"
      :agent-stages="agentStages"
      :dimensions="dimensions"
      @update:selected-file-name="selectedFileName = $event"
      @update:upload-state="uploadState = $event"
      @update:upload-error="uploadError = $event"
      @update:is-running="isRunning = $event"
      @update:preset="preset = $event"
      @update:stream-text="streamText = $event"
      @update:agent-stages="agentStages = $event"
      @update:dimensions="dimensions = $event"
      @file-selected="handleFileSelected"
      @clear-file="clearSelectedFile"
      @start-review="startReviewFlow"
      @reset-demo="resetDemo"
    />

    <ReportPage
      v-else-if="currentRoute === HASH_ROUTES.report"
      :report="report"
      :issue-state="issueState"
      :selected-issue-id="selectedIssueId"
      @issue-select="handleIssueSelection"
      @issue-status-change="handleIssueStatusChange"
      @export-suggestions="exportSuggestions"
    />

    <AssistantPage
      v-else
      :report="report"
      :session-id="sessionId"
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
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import TopNavigation from './components/layout/TopNavigation.vue'
import SideBar from './components/layout/SideBar.vue'
import WorkbenchPage from './components/pages/WorkbenchPage.vue'
import ReportPage from './components/pages/ReportPage.vue'
import AssistantPage from './components/pages/AssistantPage.vue'
import { createAgentStages, applyDimensionEvent, applyStreamingMessage, completeReporterStage } from './lib/agentStages.js'
import { buildAssistantSnapshot, createAssistantState, findIssueById, normalizeChatResponse } from './lib/assistantPanel.js'
import { sendChatMessage } from './lib/chatApi.js'
import { buildExportPayload } from './lib/exportSuggestions.js'
import { HASH_ROUTES, formatHashRoute, resolveHashRoute } from './lib/hashRoute.js'
import { buildIssueExportItems, getIssueIdentifier, mergeIssueStatuses, updateIssueStatus } from './lib/issueState.js'
import {
  createBaseDimensions,
  createEmptyReportViewModel,
  createReviewStream,
  mapReportToViewModel,
  startReview,
  uploadPrd,
} from './lib/reviewApi.js'

function getWindowHash() {
  return typeof window === 'undefined' ? '' : window.location.hash
}

function createRunState() {
  return {
    status: 'idle',
    progress: 0,
    current_dimension: null,
    completed_dimensions: [],
  }
}

const currentRoute = ref(resolveHashRoute({ hash: getWindowHash(), fallback: HASH_ROUTES.workbench }))
const selectedFile = ref(null)
const selectedFileName = ref('')
const uploadState = ref('idle')
const uploadError = ref('')
const preset = ref('normal')
const sessionId = ref('')
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

let reviewStream = null

const canViewReport = computed(() => {
  return (
    isRunning.value ||
    runState.value.status === 'completed' ||
    report.value.issues.length > 0 ||
    streamText.value.trim().length > 0
  )
})

const canOpenAssistant = computed(() => {
  return Boolean(
    sessionId.value && (runState.value.status === 'completed' || report.value.rawReport),
  )
})

const currentProject = computed(() => {
  return selectedFileName.value || report.value.rawReport?.project_name || '未选择项目'
})

const selectedIssueId = computed(() => getIssueIdentifier(selectedIssue.value) || '')
const assistantSnapshot = computed(() => {
  return buildAssistantSnapshot({
    report: report.value,
    runState: runState.value,
    selectedIssue: selectedIssue.value,
  })
})

function normalizeAccessibleRoute(route) {
  if (route === HASH_ROUTES.assistant && !canOpenAssistant.value) {
    return canViewReport.value ? HASH_ROUTES.report : HASH_ROUTES.workbench
  }

  if (route === HASH_ROUTES.report && !canViewReport.value) {
    return HASH_ROUTES.workbench
  }

  return route
}

function syncRouteFromHash() {
  const requestedRoute = resolveHashRoute({
    hash: getWindowHash(),
    fallback: HASH_ROUTES.workbench,
  })
  const nextRoute = normalizeAccessibleRoute(
    requestedRoute,
  )
  currentRoute.value = nextRoute

  if (typeof window !== 'undefined' && requestedRoute !== nextRoute) {
    window.location.hash = formatHashRoute(nextRoute)
  }
}

function goToRoute(route) {
  const nextRoute = normalizeAccessibleRoute(route)
  currentRoute.value = nextRoute

  if (typeof window === 'undefined') return

  const nextHash = formatHashRoute(nextRoute)
  if (window.location.hash !== nextHash) {
    window.location.hash = nextHash
  }
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

function closeReviewStream() {
  if (reviewStream) {
    reviewStream.close()
    reviewStream = null
  }
}

function resetReviewRun() {
  closeReviewStream()
  isRunning.value = false
  streamText.value = ''
  agentStages.value = createAgentStages()
  dimensions.value = createBaseDimensions()
  report.value = createEmptyReportViewModel()
  issueState.value = {}
  selectedIssue.value = null
  runState.value = createRunState()
  resetAssistantState()
}

function appendStreamLine(line) {
  if (!line) return
  streamText.value = streamText.value ? `${streamText.value}\n${line}` : line
}

function markDimensionStatus(dimensionName, status) {
  dimensions.value = dimensions.value.map((item) => {
    if (item.name === dimensionName) {
      return { ...item, status }
    }
    return item
  })
}

async function ensureUploadedSession() {
  if (sessionId.value) return sessionId.value

  if (!selectedFile.value) {
    throw new Error('请先选择一个 PRD 文档')
  }

  uploadState.value = 'uploading'
  uploadError.value = ''

  const result = await uploadPrd({ file: selectedFile.value })
  sessionId.value = result.session_id
  uploadState.value = 'uploaded'
  return sessionId.value
}

function handleFileSelected(file) {
  selectedFile.value = file || null
  selectedFileName.value = file?.name || ''
  sessionId.value = ''
  uploadError.value = ''
  uploadState.value = file ? 'ready' : 'idle'
  resetReviewRun()
  goToRoute(HASH_ROUTES.workbench)
}

function clearSelectedFile() {
  selectedFile.value = null
  selectedFileName.value = ''
  sessionId.value = ''
  uploadError.value = ''
  uploadState.value = 'idle'
  resetReviewRun()
  goToRoute(HASH_ROUTES.workbench)
}

function resetDemo() {
  sessionId.value = ''
  uploadError.value = ''
  uploadState.value = selectedFile.value ? 'ready' : 'idle'
  resetReviewRun()
  goToRoute(HASH_ROUTES.workbench)
}

function openReviewStream(activeSessionId) {
  closeReviewStream()

  reviewStream = createReviewStream({
    sessionId: activeSessionId,
    onConnected() {
      runState.value = {
        ...runState.value,
        status: 'reviewing',
      }
    },
    onDimensionStart(payload) {
      markDimensionStatus(payload.dimension, 'active')
      agentStages.value = applyDimensionEvent(agentStages.value, 'start', payload.dimension)
      runState.value = {
        ...runState.value,
        status: 'reviewing',
        current_dimension: payload.dimension,
      }
    },
    onDimensionComplete(payload) {
      markDimensionStatus(payload.dimension, 'complete')
      agentStages.value = applyDimensionEvent(agentStages.value, 'complete', payload.dimension)

      const completedDimensions = Array.from(
        new Set([...runState.value.completed_dimensions, payload.dimension]),
      )

      runState.value = {
        ...runState.value,
        status: 'reviewing',
        current_dimension: payload.dimension,
        completed_dimensions: completedDimensions,
        progress: Math.round((completedDimensions.length / dimensions.value.length) * 100),
      }
    },
    onStreaming(payload) {
      const content = payload?.content || ''
      appendStreamLine(content)
      agentStages.value = applyStreamingMessage(agentStages.value, content)
    },
    onComplete(payload) {
      closeReviewStream()
      isRunning.value = false
      runState.value = {
        ...runState.value,
        status: 'completed',
        progress: 100,
        current_dimension: null,
      }
      agentStages.value = completeReporterStage(agentStages.value)
      report.value = mapReportToViewModel(payload)
      issueState.value = mergeIssueStatuses(issueState.value, report.value.issues)
      goToRoute(HASH_ROUTES.report)
    },
    onError(payload) {
      appendStreamLine(payload?.message || '评审连接异常')

      if (payload?.recoverable) {
        runState.value = {
          ...runState.value,
          status: 'reviewing',
        }
        return
      }

      closeReviewStream()
      isRunning.value = false
      runState.value = {
        ...runState.value,
        status: 'error',
      }
      uploadError.value = payload?.message || '评审失败，请稍后重试'
    },
  })
}

async function startReviewFlow() {
  if (isRunning.value) return

  if (!selectedFile.value) {
    uploadState.value = 'error'
    uploadError.value = '请先选择一个 PRD 文档'
    return
  }

  resetReviewRun()
  isRunning.value = true
  runState.value = {
    ...createRunState(),
    status: 'uploading',
  }

  try {
    const activeSessionId = await ensureUploadedSession()
    await startReview({
      sessionId: activeSessionId,
      preset: preset.value,
    })

    runState.value = {
      ...createRunState(),
      status: 'reviewing',
    }
    openReviewStream(activeSessionId)
    goToRoute(HASH_ROUTES.report)
  } catch (error) {
    closeReviewStream()
    isRunning.value = false
    uploadState.value = 'error'
    uploadError.value = error instanceof Error ? error.message : '评审启动失败'
    runState.value = {
      ...runState.value,
      status: 'error',
    }
  }
}

function handleIssueSelection(issueOrId) {
  const nextIssue =
    typeof issueOrId === 'string' ? findIssueById(report.value, issueOrId) : issueOrId

  if (!nextIssue) return
  selectedIssue.value = nextIssue
}

function handleIssueStatusChange(payload) {
  const issueId = payload?.issueId || getIssueIdentifier(payload?.issue)
  if (!issueId) return
  issueState.value = updateIssueStatus(issueState.value, issueId, payload.status)
}

function exportSuggestions() {
  const exportPayload = buildExportPayload({
    fileName: 'prd-review-suggestions.md',
    issues: buildIssueExportItems(report.value.issues, issueState.value),
  })

  if (typeof document === 'undefined') return

  const blob = new Blob([exportPayload.content], { type: exportPayload.mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = exportPayload.fileName
  link.click()
  URL.revokeObjectURL(url)
}

function addChatMessage(role, content, extra = {}) {
  chatMessages.value = [
    ...chatMessages.value,
    {
      role,
      content,
      timestamp: new Date().toISOString(),
      ...extra,
    },
  ]
}

function resolveSelectedIssueId() {
  return selectedIssue.value?.issueKey || selectedIssue.value?.displayId || selectedIssue.value?.id || null
}

async function submitChatMessage(message) {
  const content = String(message || '').trim()
  if (!content) return

  if (!sessionId.value) {
    addChatMessage('system', '完成一次评审后，才能继续在助手里追问。')
    return
  }

  addChatMessage('user', content)
  isChatLoading.value = true

  try {
    const normalized = normalizeChatResponse(
      await sendChatMessage({
        sessionId: sessionId.value,
        message: content,
        selectedIssueId: resolveSelectedIssueId(),
      }),
    )

    assistantSuggestedActions.value = normalized.suggestedActions
    assistantSourceRefs.value = normalized.sourceRefs
    assistantStatus.value = normalized.assistantStatus
    assistantResponseMode.value = normalized.responseMode

    const targetIssue =
      findIssueById(report.value, normalized.targetIssueId) ||
      findIssueById(
        report.value,
        normalized.selectedIssue?.issueKey ||
          normalized.selectedIssue?.displayId ||
          normalized.selectedIssue?.id,
      )

    if (targetIssue) {
      selectedIssue.value = targetIssue
    }

    addChatMessage('assistant', normalized.message || '助手未返回可展示的内容。', {
      sourceRefs: normalized.sourceRefs,
    })
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

  if (action.type === 'rerun') {
    goToRoute(HASH_ROUTES.workbench)
    await startReviewFlow()
    return
  }

  if (action.type === 'focus_issue' && action.issue_id) {
    handleIssueSelection(action.issue_id)
    goToRoute(HASH_ROUTES.report)
    return
  }

  if (action.type === 'retry_chat') {
    const lastUserMessage = [...chatMessages.value].reverse().find((item) => item.role === 'user')
    if (lastUserMessage) {
      await submitChatMessage(lastUserMessage.content)
    }
    return
  }

  if (action.type === 'switch_preset' && action.preset) {
    preset.value = action.preset
    goToRoute(HASH_ROUTES.workbench)
    return
  }

  if (action.type === 'generate_suggestion') {
    await submitChatMessage('给我修改建议')
    return
  }

  if (action.label) {
    await submitChatMessage(action.label)
  }
}

watch(
  () => report.value.issues,
  (issues) => {
    issueState.value = mergeIssueStatuses(issueState.value, issues || [])

    if (!selectedIssue.value) return
    selectedIssue.value = findIssueById(report.value, selectedIssueId.value)
  },
  { deep: true },
)

onMounted(() => {
  if (typeof window === 'undefined') return
  syncRouteFromHash()
  window.addEventListener('hashchange', syncRouteFromHash)
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('hashchange', syncRouteFromHash)
  }
  closeReviewStream()
})
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: #fef8f1;
}

.route-actions {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 950;
}

.route-button {
  border: 1px solid #d8e1ef;
  background: #ffffff;
  border-radius: 999px;
  padding: 10px 15px;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
}

.route-button.primary {
  border-color: #3a2e47;
  background: linear-gradient(to right, #3a2e47, #51445f);
  color: #ffffff;
}

.route-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 1180px) {
  .route-actions {
    left: 20px;
    right: auto;
  }
}
</style>
