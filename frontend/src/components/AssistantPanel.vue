<template>
  <section class="assistant-panel" aria-labelledby="conversation-title">
    <header class="conversation-heading">
      <div>
        <p class="eyebrow">Conversation</p>
        <h2 id="conversation-title">围绕报告继续追问</h2>
      </div>
      <div class="assistant-state">
        <i :class="assistantStatus"></i>
        <span>{{ assistantStatusLabel }}</span>
      </div>
    </header>

    <div v-if="selectedIssue" class="focus-context">
      <div>
        <span>当前聚焦</span>
        <strong>{{ selectedIssue.displayId || selectedIssue.id }} · {{ selectedIssue.title }}</strong>
      </div>
      <button type="button" @click="$emit('open-report')">
        查看问题
      </button>
    </div>

    <div class="message-list" role="log" aria-live="polite">
      <article v-if="!chatMessages.length" class="message-row assistant welcome-message">
        <div class="avatar" aria-hidden="true">AI</div>
        <div class="message-body">
          <div class="message-meta">
            <strong>评审助手</strong>
            <span>现在</span>
          </div>
          <div class="message-bubble">
            <p>
              当前报告综合评分为 {{ snapshot.score }}/100，建议为“{{ snapshot.suggestion }}”。
              你可以让我解释结论、定位原文，或给出能直接写回 PRD 的修改稿。
            </p>
          </div>
        </div>
      </article>

      <article
        v-for="(message, index) in chatMessages"
        :key="`${message.role}-${message.timestamp || index}`"
        class="message-row"
        :class="message.role"
      >
        <div class="avatar" aria-hidden="true">{{ avatarLabel(message.role) }}</div>
        <div class="message-body">
          <div class="message-meta">
            <strong>{{ roleLabel(message.role) }}</strong>
            <span v-if="message.timestamp">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-bubble">
            <p>{{ message.content }}</p>
            <div v-if="message.sourceRefs?.length" class="message-sources">
              <button
                v-for="ref in message.sourceRefs"
                :key="sourceKey(ref)"
                type="button"
                @click="openSource(ref)"
              >
                {{ sourceLabel(ref) }}
              </button>
            </div>
          </div>
        </div>
      </article>

      <article v-if="isLoading" class="message-row assistant loading-row">
        <div class="avatar" aria-hidden="true">AI</div>
        <div class="message-body">
          <div class="message-meta"><strong>评审助手</strong></div>
          <div class="message-bubble typing-indicator" aria-label="助手正在回复">
            <i></i><i></i><i></i>
          </div>
        </div>
      </article>
    </div>

    <form class="composer" @submit.prevent="submit">
      <div v-if="actionsToShow.length" class="suggested-actions">
        <button
          v-for="action in actionsToShow.slice(0, 3)"
          :key="actionKey(action)"
          type="button"
          :disabled="isLoading"
          @click="$emit('run-action', action)"
        >
          {{ action.label }}
        </button>
      </div>

      <textarea
        v-model="draft"
        rows="3"
        :disabled="!canChat || isLoading"
        :placeholder="canChat ? '输入问题，例如：请把这个问题改写成可验收的需求描述…' : '返回工作台填写 API Key 后即可继续追问'"
        @keydown.meta.enter.prevent="submit"
        @keydown.ctrl.enter.prevent="submit"
      ></textarea>

      <footer class="composer-footer">
        <div class="starter-prompts">
          <button
            v-for="prompt in starterPrompts"
            :key="prompt"
            type="button"
            :disabled="!canChat || isLoading"
            @click="sendStarterPrompt(prompt)"
          >
            {{ prompt }}
          </button>
        </div>
        <div class="send-area">
          <span>⌘ / Ctrl + Enter</span>
          <button class="send-button" type="submit" :disabled="!canSubmit">
            {{ isLoading ? '回复中…' : '发送' }} <b aria-hidden="true">↗</b>
          </button>
        </div>
      </footer>
    </form>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['send-message', 'run-action', 'select-issue', 'open-report'])

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
      status: 'idle',
      progress: 0,
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
const starterPrompts = ['总结最重要的三点', '定位问题原文', '给出可复制修改稿']

const actionsToShow = computed(() => {
  if (props.suggestedActions.length) return props.suggestedActions
  return [{ type: 'generate_suggestion', label: '生成修改建议' }]
})

const assistantStatusLabel = computed(() => {
  const statusLabels = {
    model: '模型可用',
    unavailable: '等待模型配置',
    error: '模型请求异常',
  }
  const modeLabels = {
    model: '个性化回复',
    report_level: '报告上下文',
    error: '请求失败',
  }
  return `${statusLabels[props.assistantStatus] || '状态未知'} · ${modeLabels[props.responseMode] || '上下文未知'}`
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
  if (ref.type === 'issue') return ref.id ? `${ref.id}${ref.name ? ` · ${ref.name}` : ''}` : '问题'
  return ref.name || '原文片段'
}

function roleLabel(role) {
  return { user: '你', assistant: '评审助手', system: '系统' }[role] || role
}

function avatarLabel(role) {
  return { user: '你', assistant: 'AI', system: '!' }[role] || '•'
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function openSource(ref) {
  if (ref.type === 'issue' && ref.id) emit('select-issue', ref.id)
}
</script>

<style scoped>
.assistant-panel {
  min-height: 640px;
  padding: 26px 30px 22px;
  display: flex;
  flex-direction: column;
  border: 1px solid #e6dfd7;
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 18px 44px rgba(31, 24, 23, 0.06);
}

.conversation-heading {
  padding-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  border-bottom: 1px solid #ece6df;
}

.eyebrow {
  margin: 0 0 7px;
  color: #978f98;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.25em;
  text-transform: uppercase;
}

h2,
p {
  margin: 0;
}

h2 {
  color: #3a2e47;
  font-size: 1.15rem;
  letter-spacing: -0.02em;
}

.assistant-state {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #665974;
  font-size: 0.67rem;
  font-weight: 700;
}

.assistant-state i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d58a18;
}

.assistant-state i.model { background: #2f8a5d; }
.assistant-state i.error { background: #ba1a1a; }

.focus-context {
  margin-top: 16px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  border-left: 3px solid #3a2e47;
  border-radius: 9px;
  background: #f8f3ec;
}

.focus-context div {
  min-width: 0;
  display: grid;
  gap: 3px;
}

.focus-context span {
  color: #8c848d;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.focus-context strong {
  overflow: hidden;
  color: #3a2e47;
  font-size: 0.78rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.focus-context button {
  flex: 0 0 auto;
  border: 0;
  background: transparent;
  color: #3a2e47;
  cursor: pointer;
  font-size: 0.68rem;
  font-weight: 800;
}

.message-list {
  flex: 1;
  min-height: 390px;
  max-height: 570px;
  padding: 26px 8px 38px 2px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(58, 46, 71, 0.16) transparent;
}

.message-row {
  max-width: min(760px, 88%);
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
  align-self: flex-start;
}

.message-row.user {
  grid-template-columns: minmax(0, 1fr) 34px;
  align-self: flex-end;
}

.message-row.user .avatar {
  grid-column: 2;
}

.message-row.user .message-body {
  grid-column: 1;
  grid-row: 1;
}

.avatar {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #3a2e47;
  color: #fff;
  font-size: 0.65rem;
  font-weight: 850;
}

.user .avatar {
  background: #f4bd69;
  color: #3c2600;
}

.system .avatar {
  background: #ba1a1a;
}

.message-body {
  min-width: 0;
  display: grid;
  gap: 7px;
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: #8c848d;
  font-size: 0.65rem;
}

.message-meta strong {
  color: #3a2e47;
  font-size: 0.7rem;
}

.user .message-meta {
  flex-direction: row-reverse;
}

.message-bubble {
  padding: 15px 17px;
  border-radius: 4px 16px 16px 16px;
  background: #f8f3ec;
  color: #454047;
  font-size: 0.86rem;
  line-height: 1.78;
}

.user .message-bubble {
  border-radius: 16px 4px 16px 16px;
  background: #3a2e47;
  color: #fff;
}

.system .message-bubble {
  background: #fff4d9;
}

.message-bubble p {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-sources {
  margin-top: 11px;
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.message-sources button {
  padding: 5px 9px;
  border: 1px solid #d1c0e1;
  border-radius: 999px;
  background: #fff;
  color: #3a2e47;
  cursor: pointer;
  font-size: 0.62rem;
  font-weight: 750;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
}

.typing-indicator i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #8c848d;
  animation: typing 1s infinite ease-in-out;
}

.typing-indicator i:nth-child(2) { animation-delay: 120ms; }
.typing-indicator i:nth-child(3) { animation-delay: 240ms; }

@keyframes typing {
  0%, 70%, 100% { transform: translateY(0); opacity: .45; }
  35% { transform: translateY(-4px); opacity: 1; }
}

.composer {
  position: sticky;
  bottom: 0;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 16px 46px rgba(31, 24, 23, 0.13);
  backdrop-filter: blur(18px);
}

.suggested-actions,
.starter-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.suggested-actions {
  padding: 2px 3px 8px;
}

.suggested-actions button,
.starter-prompts button {
  padding: 6px 10px;
  border: 1px solid #e1d8e7;
  border-radius: 999px;
  background: #fff;
  color: #665974;
  cursor: pointer;
  font-size: 0.63rem;
  font-weight: 700;
}

.composer textarea {
  width: 100%;
  min-height: 88px;
  padding: 12px 13px;
  resize: vertical;
  border: 0;
  outline: 0;
  background: transparent;
  color: #1d1b17;
  font: inherit;
  font-size: 0.86rem;
  line-height: 1.65;
}

.composer textarea::placeholder {
  color: #9c949d;
}

.composer-footer {
  padding: 9px 4px 2px;
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
  border-top: 1px solid #eee8e1;
}

.send-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.send-area > span {
  color: #a39ba4;
  font-size: 0.58rem;
  white-space: nowrap;
}

.send-button {
  min-width: 96px;
  min-height: 40px;
  padding: 0 17px;
  border: 0;
  border-radius: 999px;
  background: #3a2e47;
  color: #fff;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 800;
}

.send-button b {
  margin-left: 5px;
}

button:disabled,
textarea:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

@media (max-width: 720px) {
  .assistant-panel {
    min-height: 560px;
    padding: 22px 18px 16px;
  }

  .conversation-heading,
  .composer-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .message-row {
    max-width: 96%;
  }

  .send-area {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
