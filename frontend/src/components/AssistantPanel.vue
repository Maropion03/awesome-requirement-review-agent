<template>
  <aside class="panel">
    <header class="panel-header">
      <div>
        <p class="eyebrow">Guided Assistant</p>
        <h2>对话式评审助手</h2>
        <p class="subtitle">你可以问结论、问原文、点问题，或直接让助手帮你重跑。</p>
      </div>
      <div class="status-stack">
        <span class="status-pill" :class="snapshot.status">{{ statusLabel }}</span>
        <span class="mode-pill" :class="assistantStatus">{{ assistantStatusLabel }}</span>
      </div>
    </header>

    <section class="snapshot-grid compact">
      <div class="snapshot-card primary">
        <span class="label">综合评分</span>
        <strong>{{ snapshot.score }}/10</strong>
        <p>{{ snapshot.suggestion }}</p>
      </div>
      <div class="snapshot-card">
        <span class="label">运行状态</span>
        <strong>{{ statusLabel }}</strong>
        <p>{{ snapshot.progress }}%</p>
      </div>
    </section>

    <section class="thread prominent">
      <div class="section-head compact">
        <h3>对话</h3>
        <span class="muted">{{ chatMessages.length }} 条</span>
      </div>

      <div class="messages">
        <article
          v-for="(message, index) in chatMessages"
          :key="`${message.role}-${index}`"
          class="message"
          :class="message.role"
        >
          <div class="message-head">
            <strong>{{ roleLabel(message.role) }}</strong>
            <span v-if="message.timestamp" class="muted">{{ formatTime(message.timestamp) }}</span>
          </div>
          <p>{{ message.content }}</p>

          <div v-if="message.sourceRefs?.length" class="mini-sources">
            <button
              v-for="ref in message.sourceRefs"
              :key="sourceKey(ref)"
              class="source-chip"
              type="button"
              @click="openSource(ref)"
            >
              {{ sourceLabel(ref) }}
            </button>
          </div>
        </article>

        <p v-if="!chatMessages.length" class="empty-state">
          先问我“为什么是这个结论”或者“这个问题在哪一段”。
        </p>
      </div>
    </section>

    <details class="collapsible">
      <summary>
        <span>上下文</span>
        <span class="summary-meta">
          <span class="summary-cue">查看</span>
          <span class="muted">{{ sourceRefs.length }} 条</span>
          <span class="summary-arrow" aria-hidden="true"></span>
        </span>
      </summary>

      <div class="details-body">
        <div v-if="selectedIssue" class="selected-issue">
          <strong>{{ selectedIssue.displayId || selectedIssue.id }} · {{ selectedIssue.title }}</strong>
          <p>{{ selectedIssue.description }}</p>
        </div>

        <div v-if="sourceRefs.length" class="source-list">
          <article v-for="ref in sourceRefs" :key="sourceKey(ref)" class="source-card">
            <div class="source-top">
              <strong>{{ sourceLabel(ref) }}</strong>
              <button
                v-if="ref.type === 'issue' && ref.id"
                class="link-button"
                type="button"
                @click="$emit('select-issue', ref.id)"
              >
                聚焦
              </button>
            </div>
            <p v-if="ref.excerpt" class="source-excerpt">{{ ref.excerpt }}</p>
          </article>
        </div>

        <div v-else class="source-list">
          <article class="source-card">
            <p class="source-excerpt">这里会显示当前问题和 PRD 原文的引用片段。</p>
          </article>
        </div>
      </div>
    </details>

    <details class="collapsible">
      <summary>
        <span>建议动作</span>
        <span class="summary-meta">
          <span class="summary-cue">展开</span>
          <span class="muted">{{ actionsToShow.length }} 项</span>
          <span class="summary-arrow" aria-hidden="true"></span>
        </span>
      </summary>

      <div class="details-body">
        <div class="chip-row">
          <button
            v-for="action in actionsToShow"
            :key="actionKey(action)"
            class="chip"
            type="button"
            @click="$emit('run-action', action)"
          >
            {{ action.label }}
          </button>
        </div>
      </div>
    </details>

    <form class="composer composer-prominent" @submit.prevent="submit">
      <textarea
        v-model="draft"
        class="composer-input"
        rows="5"
        :disabled="!canChat || isLoading"
        placeholder="问我：为什么这样判、原文在哪里、怎么改更合适..."
      ></textarea>
      <div class="composer-footer">
        <div class="starter-prompts">
          <button
            v-for="prompt in starterPrompts"
            :key="prompt"
            class="starter-chip"
            type="button"
            :disabled="!canChat || isLoading"
            @click="sendStarterPrompt(prompt)"
          >
            {{ prompt }}
          </button>
        </div>
        <button class="send-button" type="submit" :disabled="!canSubmit">
          {{ isLoading ? '发送中...' : '发送' }}
        </button>
      </div>
    </form>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['send-message', 'run-action', 'select-issue'])

const props = defineProps({
  chatMessages: {
    type: Array,
    default: () => [],
  },
  snapshot: {
    type: Object,
    default: () => ({
      score: '--',
      suggestion: '尚未生成',
      summary: '评审完成后将在这里显示结论。',
      status: 'idle',
      progress: 0,
      currentDimension: null,
      selectedIssue: null,
    }),
  },
  suggestedActions: {
    type: Array,
    default: () => [],
  },
  sourceRefs: {
    type: Array,
    default: () => [],
  },
  selectedIssue: {
    type: Object,
    default: null,
  },
  assistantStatus: {
    type: String,
    default: 'unavailable',
  },
  responseMode: {
    type: String,
    default: 'report_level',
  },
  canChat: {
    type: Boolean,
    default: false,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
})

const draft = ref('')
const starterPrompts = ['解释当前结论', '定位问题原文', '给我修改建议']

const actionsToShow = computed(() => {
  if (props.suggestedActions.length) return props.suggestedActions

  return [
    { type: 'rerun', label: '重新评审' },
    { type: 'generate_suggestion', label: '生成修改建议' },
  ]
})

const statusLabel = computed(() => {
  const labels = {
    idle: '等待输入',
    uploading: '上传中',
    reviewing: '评审中',
    completed: '已完成',
    error: '异常',
  }

  return labels[props.snapshot.status] || props.snapshot.status || '未知'
})

const assistantStatusLabel = computed(() => {
  const labels = {
    model: '模型可用',
    unavailable: '模型未接入',
    error: '模型异常',
  }

  const responseModeLabels = {
    model: '已走个性化回复',
    report_level: '报告级回复',
    error: '回退到报告级',
  }

  const statusLabelText = labels[props.assistantStatus] || props.assistantStatus || '未知'
  const modeLabelText = responseModeLabels[props.responseMode] || props.responseMode || '未识别'
  return `${statusLabelText} · ${modeLabelText}`
})

const canSubmit = computed(() => props.canChat && !props.isLoading && draft.value.trim().length > 0)

function submit() {
  if (!canSubmit.value) return
  emit('send-message', draft.value.trim())
  draft.value = ''
}

function sendStarterPrompt(prompt) {
  if (!props.canChat || props.isLoading) return
  emit('send-message', prompt)
}

function actionKey(action) {
  return `${action.type}-${action.label}-${action.issue_id || action.preset || ''}`
}

function sourceKey(ref) {
  return `${ref.type}-${ref.id || ref.name || ref.excerpt || ''}`
}

function sourceLabel(ref) {
  if (ref.type === 'issue') {
    return ref.id ? `${ref.id}${ref.name ? ` · ${ref.name}` : ''}` : '问题'
  }

  return ref.name || '原文片段'
}

function roleLabel(role) {
  const labels = {
    user: '你',
    assistant: '助手',
    system: '系统',
  }

  return labels[role] || role
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function openSource(ref) {
  if (ref.type === 'issue' && ref.id) {
    emit('select-issue', ref.id)
  }
}
</script>

<style scoped>
.panel {
  display: grid;
  gap: 14px;
  padding: 16px;
  border: 1px solid #cfe0f7;
  border-radius: 22px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

.status-stack {
  display: grid;
  gap: 6px;
  justify-items: end;
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

h2,
h3,
p {
  margin: 0;
}

.subtitle,
.muted {
  color: #64748b;
}

.status-pill {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #e2e8f0;
  color: #334155;
}

.mode-pill {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #475569;
}

.mode-pill.model {
  background: #dcfce7;
  color: #166534;
  border-color: #86efac;
}

.mode-pill.unavailable {
  background: #fef3c7;
  color: #92400e;
  border-color: #fcd34d;
}

.mode-pill.error {
  background: #fee2e2;
  color: #b91c1c;
  border-color: #fca5a5;
}

.status-pill.reviewing {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-pill.completed {
  background: #dcfce7;
  color: #15803d;
}

.status-pill.error {
  background: #fee2e2;
  color: #b91c1c;
}

.snapshot-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.snapshot-grid.compact {
  gap: 8px;
}

.snapshot-card {
  border: 1px solid #d8e1ef;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
  display: grid;
  gap: 4px;
}

.snapshot-card.primary {
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.snapshot-card strong {
  font-size: 16px;
  color: #0f172a;
}

.label {
  font-size: 12px;
  color: #64748b;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.section-head.compact h3 {
  font-size: 15px;
}

.thread,
.composer {
  display: grid;
  gap: 10px;
}

.thread.prominent {
  gap: 12px;
  padding: 14px;
  border: 1px solid #bfd7ff;
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.chip-row,
.starter-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip,
.starter-chip,
.source-chip,
.send-button,
.link-button {
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 999px;
  padding: 8px 12px;
  cursor: pointer;
}

.chip,
.starter-chip {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.messages {
  display: grid;
  gap: 10px;
  min-height: 360px;
  max-height: 520px;
  overflow: auto;
  padding: 4px 6px 4px 2px;
}

.message {
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #d8e1ef;
  background: #fff;
  display: grid;
  gap: 8px;
  line-height: 1.6;
}

.message.user {
  background: #e8f1ff;
  border-color: #bcd3ff;
}

.message.assistant {
  background: #f8fafc;
  border-color: #d6e2f3;
}

.message.system {
  background: #fefce8;
}

.message-head,
.source-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.mini-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.empty-state {
  color: #94a3b8;
}

.selected-issue,
.source-card {
  border: 1px solid #d8e1ef;
  border-radius: 12px;
  background: #fff;
  padding: 10px;
  display: grid;
  gap: 8px;
}

.source-excerpt {
  color: #334155;
  white-space: pre-wrap;
  line-height: 1.5;
}

.composer-prominent {
  gap: 12px;
  padding: 14px;
  border: 1px solid #bfdbfe;
  border-radius: 18px;
  background: linear-gradient(180deg, #eef6ff 0%, #ffffff 100%);
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.08);
}

.composer-input {
  width: 100%;
  min-height: 132px;
  resize: vertical;
  border: 1px solid #bcd3ff;
  border-radius: 16px;
  padding: 14px 16px;
  font: inherit;
  line-height: 1.6;
  color: #0f172a;
  background: #fff;
  box-sizing: border-box;
}

.composer-input:focus {
  outline: 2px solid rgba(37, 99, 235, 0.18);
  border-color: #2563eb;
}

.composer-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.starter-prompts {
  flex: 1 1 420px;
}

.send-button {
  min-width: 120px;
  min-height: 46px;
  padding: 10px 18px;
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
  font-weight: 600;
}

.starter-chip {
  padding: 8px 14px;
}

.chip,
.source-chip,
.link-button {
  padding: 8px 12px;
}

.send-button:disabled,
.chip:disabled,
.starter-chip:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.link-button {
  padding: 6px 10px;
  background: transparent;
  border-color: transparent;
  color: #2563eb;
}

.collapsible {
  border: 1px solid #d8e1ef;
  border-radius: 12px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.8);
}

.collapsible summary {
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  list-style: none;
  font-weight: 600;
}

.summary-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.summary-cue {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.summary-arrow {
  width: 8px;
  height: 8px;
  border-right: 2px solid #2563eb;
  border-bottom: 2px solid #2563eb;
  transform: rotate(45deg);
  transition: transform 0.18s ease;
  margin-top: -3px;
}

.collapsible summary::-webkit-details-marker {
  display: none;
}

.collapsible[open] .summary-arrow {
  transform: rotate(225deg);
  margin-top: 3px;
}

.details-body {
  margin-top: 8px;
  display: grid;
  gap: 8px;
}

@media (max-width: 1024px) {
  .snapshot-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 720px) {
  .snapshot-grid {
    grid-template-columns: 1fr;
  }

  .messages {
    min-height: 280px;
    max-height: 440px;
  }

  .composer-footer {
    align-items: stretch;
  }

  .send-button {
    width: 100%;
  }
}
</style>
