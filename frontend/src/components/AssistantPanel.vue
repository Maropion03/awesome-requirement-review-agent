<template>
  <section class="assistant-panel surface-card" aria-labelledby="conversation-title">
    <header class="conversation-heading">
      <div><p class="overline">Conversation</p><h2 id="conversation-title">围绕报告继续追问</h2></div>
      <div class="assistant-state"><i :class="assistantStatus"></i><span>{{ assistantStatusLabel }}</span></div>
    </header>

    <div v-if="selectedIssue" class="focus-context">
      <div><span>当前聚焦</span><strong>{{ selectedIssue.displayId || selectedIssue.id }} · {{ selectedIssue.title }}</strong></div>
      <button type="button" @click="$emit('open-report')">查看问题</button>
    </div>

    <div class="message-list" role="log" aria-live="polite">
      <article v-if="!chatMessages.length" class="message-row assistant">
        <div class="avatar">AI</div>
        <div class="message-body"><div class="message-meta"><strong>评审助手</strong><span>现在</span></div><div class="message-bubble"><p>当前报告综合评分为 {{ snapshot.score }}/100，建议为“{{ snapshot.suggestion }}”。你可以让我解释结论、定位原文，或给出能直接写回 PRD 的修改稿。</p></div></div>
      </article>

      <article v-for="(message, index) in chatMessages" :key="`${message.role}-${message.timestamp || index}`" class="message-row" :class="message.role">
        <div class="avatar">{{ avatarLabel(message.role) }}</div>
        <div class="message-body">
          <div class="message-meta"><strong>{{ roleLabel(message.role) }}</strong><span v-if="message.timestamp">{{ formatTime(message.timestamp) }}</span></div>
          <div class="message-bubble">
            <p>{{ message.content }}</p>
            <div v-if="message.sourceRefs?.length" class="message-sources"><button v-for="ref in message.sourceRefs" :key="sourceKey(ref)" type="button" @click="openSource(ref)">{{ sourceLabel(ref) }}</button></div>
          </div>
        </div>
      </article>

      <article v-if="isLoading" class="message-row assistant">
        <div class="avatar">AI</div><div class="message-body"><div class="message-meta"><strong>评审助手</strong></div><div class="message-bubble typing-indicator"><i></i><i></i><i></i></div></div>
      </article>
    </div>

    <form class="composer" @submit.prevent="submit">
      <div v-if="actionsToShow.length" class="suggested-actions"><button v-for="action in actionsToShow.slice(0, 3)" :key="actionKey(action)" type="button" :disabled="isLoading" @click="$emit('run-action', action)">{{ action.label }}</button></div>
      <textarea v-model="draft" rows="4" :disabled="!canChat || isLoading" :placeholder="canChat ? '继续追问，例如：请给出这个问题的修改建议' : '在 API 设置页填写 Key 后即可继续追问'" @keydown.meta.enter.prevent="submit" @keydown.ctrl.enter.prevent="submit"></textarea>
      <footer class="composer-footer">
        <div class="starter-prompts"><button v-for="prompt in starterPrompts" :key="prompt" type="button" :disabled="!canChat || isLoading" @click="sendStarterPrompt(prompt)">{{ prompt.label }}</button></div>
        <button class="send-button" type="submit" :disabled="!canSubmit">{{ isLoading ? '回复中…' : '发送' }}</button>
      </footer>
    </form>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
const emit = defineEmits(['send-message', 'run-action', 'select-issue', 'open-report'])
const props = defineProps({
  chatMessages: { type: Array, default: () => [] }, snapshot: { type: Object, default: () => ({ score: '--', suggestion: '尚未生成' }) },
  suggestedActions: { type: Array, default: () => [] }, sourceRefs: { type: Array, default: () => [] }, selectedIssue: { type: Object, default: null },
  assistantStatus: { type: String, default: 'unavailable' }, responseMode: { type: String, default: 'report_level' }, canChat: Boolean, isLoading: Boolean,
})
const draft = ref('')
const starterPrompts = [
  { label: '总结三点', value: '请总结最重要的三个修改点' }, { label: '修改建议', value: '请给出详细修改建议' }, { label: '影响范围', value: '这个问题会影响哪些业务流程' },
]
const actionsToShow = computed(() => props.suggestedActions.length ? props.suggestedActions : [{ type: 'generate_suggestion', label: '生成修改建议' }])
const assistantStatusLabel = computed(() => ({ model: '模型可用 · 个性化回复', unavailable: '等待模型配置', error: '模型请求异常' }[props.assistantStatus] || '状态未知'))
const canSubmit = computed(() => props.canChat && !props.isLoading && draft.value.trim().length > 0)
function submit() { if (!canSubmit.value) return; emit('send-message', draft.value.trim()); draft.value = '' }
function sendStarterPrompt(prompt) { if (props.canChat && !props.isLoading) emit('send-message', prompt.value) }
function actionKey(action) { return `${action.type}-${action.label}-${action.issue_id || ''}` }
function sourceKey(ref) { return `${ref.type}-${ref.id || ref.name || ref.excerpt || ''}` }
function sourceLabel(ref) { return ref.type === 'issue' ? (ref.id ? `${ref.id}${ref.name ? ` · ${ref.name}` : ''}` : '问题') : (ref.name || '原文片段') }
function roleLabel(role) { return { user: '你', assistant: '评审助手', system: '系统' }[role] || role }
function avatarLabel(role) { return { user: '你', assistant: 'AI', system: '!' }[role] || '•' }
function formatTime(timestamp) { const date = new Date(timestamp); return Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }
function openSource(ref) { if (ref.type === 'issue' && ref.id) emit('select-issue', ref.id) }
</script>

<style scoped>
.assistant-panel { min-height: 620px; padding: 24px; display: flex; flex-direction: column; }
.conversation-heading { padding-bottom: 18px; display: flex; align-items: center; justify-content: space-between; gap: 20px; border-bottom: 1px solid var(--line); }
h2 { margin: 8px 0 0; font-size: 20px; }
.assistant-state { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 11px; font-weight: 700; }.assistant-state i { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }.assistant-state i.model { background: var(--success); }.assistant-state i.error { background: var(--danger); }
.focus-context { margin-top: 16px; padding: 12px 14px; display: flex; align-items: center; justify-content: space-between; gap: 14px; border-radius: 15px; background: var(--soft); }
.focus-context div { min-width: 0; display: grid; gap: 4px; }.focus-context span { color: var(--muted); font-size: 9px; font-weight: 800; letter-spacing: .12em; }.focus-context strong { overflow: hidden; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }.focus-context button { border: 0; background: transparent; color: var(--primary); cursor: pointer; font-weight: 800; }
.message-list { height: 420px; padding: 24px 5px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
.message-row { max-width: 84%; display: grid; grid-template-columns: 34px minmax(0,1fr); gap: 10px; }.message-row.user { align-self: flex-end; grid-template-columns: minmax(0,1fr) 34px; }.message-row.user .avatar { grid-column: 2; }.message-row.user .message-body { grid-row: 1; grid-column: 1; }.avatar { width: 34px; height: 34px; display: grid; place-items: center; border-radius: 50%; background: var(--ink); color: #fff; font-size: 10px; font-weight: 800; }.user .avatar { background: var(--primary); }
.message-meta { margin: 0 4px 7px; display: flex; justify-content: space-between; gap: 14px; color: var(--muted); font-size: 10px; }.user .message-meta { flex-direction: row-reverse; }
.message-bubble { padding: 15px 17px; border-radius: 7px 20px 20px 20px; background: var(--soft); color: var(--ink); }.user .message-bubble { border-radius: 20px 7px 20px 20px; background: var(--primary); color: #fff; }.message-bubble p { margin: 0; white-space: pre-wrap; font-size: 13px; line-height: 1.8; }
.message-sources { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 7px; }.message-sources button, .suggested-actions button, .starter-prompts button { padding: 6px 10px; border: 1px solid var(--line); border-radius: 999px; background: #fffdf8; color: var(--primary); cursor: pointer; font-size: 10px; font-weight: 700; }
.typing-indicator { display: flex; gap: 5px; }.typing-indicator i { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); animation: pulse 1s infinite alternate; }.typing-indicator i:nth-child(2) { animation-delay: .2s; }.typing-indicator i:nth-child(3) { animation-delay: .4s; }
.composer { padding: 12px; border: 1px solid var(--line); border-radius: 25px; background: var(--soft); }.suggested-actions { padding: 3px 3px 10px; display: flex; flex-wrap: wrap; gap: 7px; }
textarea { width: 100%; box-sizing: border-box; min-height: 100px; padding: 12px; border: 0; outline: 0; resize: none; background: transparent; color: var(--ink); font: 13px/1.7 inherit; }
.composer-footer { padding: 11px 3px 3px; display: flex; align-items: center; justify-content: space-between; gap: 12px; border-top: 1px solid var(--line); }.starter-prompts { display: flex; flex-wrap: wrap; gap: 7px; }.send-button { min-height: 39px; padding: 0 20px; border: 0; border-radius: 999px; background: var(--primary); color: #fff; cursor: pointer; font-weight: 800; }.send-button:disabled, button:disabled { cursor: not-allowed; opacity: .45; }
@keyframes pulse { to { transform: translateY(-3px); opacity: .45; } }
@media (max-width: 650px) { .assistant-panel { padding: 17px; } .conversation-heading, .composer-footer { align-items: flex-start; flex-direction: column; } .message-row { max-width: 94%; } }
</style>
