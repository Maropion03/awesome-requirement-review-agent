<template>
  <div class="assistant-page">
    <header class="assistant-page-header">
      <div>
        <h2>报告摘要与评审助手</h2>
        <p class="subtitle">保留当前会话，继续追问结论、原文和修改建议。</p>
      </div>
    </header>

    <div class="assistant-content">
      <section class="assistant-summary-grid">
        <article class="assistant-summary-card primary">
          <span class="label">综合评分</span>
          <strong>{{ report.score }}/10</strong>
          <p>{{ report.summary }}</p>
        </article>
        <article class="assistant-summary-card" :class="recommendationClass">
          <span class="label">评审建议</span>
          <strong>{{ report.suggestion }}</strong>
          <p v-if="selectedIssue">当前聚焦：{{ selectedIssue.displayId || selectedIssue.id }} · {{ selectedIssue.title }}</p>
          <p v-else>点击问题或直接提问，助手会带着当前报告上下文继续回答。</p>
        </article>
        <article class="assistant-summary-card">
          <span class="label">会话状态</span>
          <strong>{{ sessionId ? '已连接' : '未开始' }}</strong>
          <p v-if="sessionId">Session：{{ sessionId.substring(0, 8) }}...</p>
          <p v-else>上传并完成一次评审后，可以继续在这里对话。</p>
        </article>
        <article class="assistant-summary-card" :class="assistantStatusClass">
          <span class="label">模型状态</span>
          <strong>{{ assistantStatusLabel }}</strong>
          <p>{{ responseModeLabel }}</p>
        </article>
      </section>

      <section class="assistant-main-area">
        <AssistantPanel
          class="assistant-panel-full"
          :chat-messages="chatMessages"
          :snapshot="assistantSnapshot"
          :suggested-actions="assistantSuggestedActions"
          :source-refs="assistantSourceRefs"
          :selected-issue="selectedIssue"
          :assistant-status="assistantStatus"
          :response-mode="assistantResponseMode"
          :can-chat="Boolean(sessionId)"
          :is-loading="isChatLoading"
          @send-message="submitChatMessage"
          @run-action="handleAssistantAction"
          @select-issue="handleIssueSelectionById"
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AssistantPanel from '../AssistantPanel.vue'

const props = defineProps({
  report: Object,
  sessionId: String,
  chatMessages: Array,
  selectedIssue: Object,
  assistantSuggestedActions: Array,
  assistantSourceRefs: Array,
  assistantStatus: String,
  assistantResponseMode: String,
  isChatLoading: Boolean,
  assistantSnapshot: Object,
})

const emit = defineEmits([
  'send-message',
  'run-action',
  'select-issue',
  'update:chat-messages',
])

const recommendationClass = computed(() => {
  const label = props.report.suggestion
  if (label === 'APPROVE' || label === '通过') return 'approve'
  if (label === 'MODIFY' || label === '修改后通过') return 'modify'
  if (label === 'REJECT' || label === '驳回') return 'reject'
  return 'pending'
})

const assistantStatusClass = computed(() => props.assistantStatus || 'unavailable')

const assistantStatusLabel = computed(() => {
  const labels = {
    model: '模型回答',
    unavailable: '模型未接入',
    error: '模型异常',
  }
  return labels[props.assistantStatus] || props.assistantStatus || '未知'
})

const responseModeLabel = computed(() => {
  const labels = {
    model: '已使用个性化模型回复',
    report_level: '当前使用报告级回复',
    error: '模型失败后回退到报告级回复',
  }
  return labels[props.assistantResponseMode] || props.assistantResponseMode || '未识别'
})

const submitChatMessage = (message) => {
  emit('send-message', message)
}

const handleAssistantAction = (action) => {
  emit('run-action', action)
}

const handleIssueSelectionById = (issueId) => {
  emit('select-issue', issueId)
}
</script>

<style scoped>
.assistant-page {
  padding: 88px 20px 20px 300px;
  background: #fef8f1;
  min-height: calc(100vh - 64px);
  display: grid;
  gap: 18px;
}

.assistant-page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
  flex-wrap: wrap;
}

.assistant-content {
  display: grid;
  gap: 18px;
}

.assistant-summary-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.assistant-summary-card {
  background: #ffffff;
  border: 1px solid #dbe3ef;
  border-radius: 1rem;
  padding: 16px;
  display: grid;
  gap: 8px;
}

.assistant-summary-card .label {
  color: #64748b;
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-weight: 500;
}

.assistant-summary-card strong {
  font-family: 'Satoshi', sans-serif;
  font-weight: 700;
  font-size: 24px;
  color: #0f172a;
}

.assistant-summary-card p {
  margin: 0;
  color: #64748b;
  font-family: 'Inter', sans-serif;
  line-height: 1.5;
  font-size: 0.875rem;
}

.assistant-summary-card.primary {
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.assistant-summary-card.approve {
  background: #f0fdf4;
  border-color: #16a34a;
}

.assistant-summary-card.modify {
  background: #fffbeb;
  border-color: #f59e0b;
}

.assistant-summary-card.reject {
  background: #fef2f2;
  border-color: #dc2626;
}

.assistant-summary-card.pending {
  background: #eff6ff;
  border-color: #2563eb;
}

.assistant-main-area {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
}

.assistant-panel-full {
  min-width: 0;
  height: 100%;
}

h2 {
  margin: 0;
  font-family: 'Satoshi', sans-serif;
  font-weight: 600;
  font-size: 1.75rem;
  color: #1d1b17;
  letter-spacing: -0.02em;
}

.subtitle {
  font-family: 'Inter', sans-serif;
  color: #64748b;
  font-size: 0.875rem;
}

@media (max-width: 1180px) {
  .assistant-page {
    padding-left: 20px;
    padding-top: 88px;
  }
}
</style>
