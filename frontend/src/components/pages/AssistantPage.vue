<template>
  <main class="page-shell assistant-page">
    <PageHeader
      title="报告摘要与追问助手"
      description="结合当前报告和选中的问题继续追问，不依赖服务端会话。"
      :can-view-report="true"
      :can-open-assistant="canChat"
      @navigate="$emit('navigate', $event)"
    />

    <section class="assistant-title-card surface-card">
      <div>
        <p class="overline">Assistant</p>
        <h1>报告摘要与追问助手</h1>
        <p>助手会带着当前报告与所选问题回答，每次请求均使用浏览器中保存的模型配置。</p>
      </div>
      <div class="title-actions">
        <button class="pill-button" type="button" @click="$emit('back-to-report')">返回报告</button>
        <button class="pill-button" type="button" @click="$emit('export-suggestions')">导出 MD</button>
        <button class="pill-button primary" type="button" @click="$emit('rerun')">重新评审</button>
      </div>
    </section>

    <div class="assistant-layout">
      <div class="assistant-main">
        <section class="assistant-stats" aria-label="助手上下文摘要">
          <article class="surface-card"><p class="overline">综合评分</p><strong>{{ report.score }}<small>/100</small></strong></article>
          <article class="surface-card"><p class="overline">评审建议</p><strong>{{ report.suggestion }}</strong></article>
          <article class="surface-card"><p class="overline">会话状态</p><strong class="status-value"><i :class="{ ready: canChat }"></i>{{ canChat ? '模型可用' : '缺少 Key' }}</strong></article>
        </section>

        <section class="selected-issue surface-card">
          <div>
            <p class="overline">Selected issue</p>
            <h2>{{ selectedIssue?.title || '未选中问题' }}</h2>
            <p>{{ selectedIssue ? `${selectedIssue.dimension} · ${selectedIssue.description}` : '从报告页选择问题后，这里会自动聚焦对应上下文。' }}</p>
          </div>
          <span>{{ selectedIssue?.displayId || selectedIssue?.id || 'N/A' }}</span>
        </section>

        <AssistantPanel
          :chat-messages="chatMessages"
          :snapshot="assistantSnapshot"
          :suggested-actions="assistantSuggestedActions"
          :source-refs="assistantSourceRefs"
          :selected-issue="selectedIssue"
          :assistant-status="assistantStatus"
          :response-mode="assistantResponseMode"
          :can-chat="canChat"
          :is-loading="isChatLoading"
          @send-message="$emit('send-message', $event)"
          @run-action="$emit('run-action', $event)"
          @select-issue="$emit('select-issue', $event)"
          @open-report="$emit('back-to-report')"
        />
      </div>

      <aside class="context-rail">
        <section class="surface-card rail-card">
          <p class="overline">Run summary</p>
          <dl>
            <div><dt>当前接口</dt><dd>{{ formatLabel || '未配置' }}</dd></div>
            <div><dt>已完成维度</dt><dd>{{ completedDimensions }}/6</dd></div>
            <div><dt>当前进度</dt><dd>{{ assistantSnapshot.progress || 0 }}%</dd></div>
          </dl>
        </section>
        <section class="surface-card rail-card">
          <p class="overline">Report summary</p>
          <p class="rail-copy">{{ report.summary || '暂无报告摘要。' }}</p>
        </section>
        <section class="surface-card rail-card">
          <div class="rail-heading"><p class="overline">Issue shortcuts</p><span>{{ issues.length }}</span></div>
          <div v-if="issues.length" class="shortcut-list">
            <button v-for="issue in issues.slice(0, 6)" :key="issue.issueKey || issue.displayId || issue.id" type="button" :class="{ active: isSelected(issue) }" @click="$emit('select-issue', issue.issueKey || issue.displayId || issue.id)">
              <span>{{ issue.displayId || issue.id }}</span><strong>{{ issue.title }}</strong>
            </button>
          </div>
          <p v-else class="rail-copy">当前报告没有问题快捷入口。</p>
        </section>
      </aside>
    </div>
  </main>
</template>

<script setup>
import { computed } from 'vue'
import AssistantPanel from '../AssistantPanel.vue'
import PageHeader from '../layout/PageHeader.vue'
import { getIssueIdentifier } from '../../lib/issueState.js'

const props = defineProps({
  report: { type: Object, default: () => ({ score: '--', suggestion: '尚未生成', summary: '', issues: [] }) },
  canChat: Boolean,
  formatLabel: String,
  chatMessages: { type: Array, default: () => [] },
  selectedIssue: Object,
  assistantSuggestedActions: { type: Array, default: () => [] },
  assistantSourceRefs: { type: Array, default: () => [] },
  assistantStatus: String,
  assistantResponseMode: String,
  isChatLoading: Boolean,
  assistantSnapshot: { type: Object, default: () => ({ progress: 0 }) },
})
defineEmits(['send-message', 'run-action', 'select-issue', 'back-to-report', 'export-suggestions', 'rerun', 'navigate'])
const issues = computed(() => props.report.issues || [])
const completedDimensions = computed(() => Math.round(((props.assistantSnapshot.progress || 0) / 100) * 6))
function isSelected(issue) { return getIssueIdentifier(issue) === getIssueIdentifier(props.selectedIssue) }
</script>

<style scoped>
.assistant-title-card { margin-bottom: 24px; padding: 24px 26px; display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
h1 { margin: 8px 0 0; font-size: 30px; letter-spacing: -.03em; }
.assistant-title-card > div > p:last-child { margin: 8px 0 0; color: var(--muted); font-size: 13px; line-height: 1.7; }
.title-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 10px; }
.assistant-layout { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(290px, .7fr); gap: 24px; }
.assistant-main, .context-rail { min-width: 0; display: grid; align-content: start; gap: 24px; }
.assistant-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.assistant-stats article { padding: 20px; }
.assistant-stats strong { display: block; margin-top: 12px; color: var(--primary); font-size: 25px; }
.assistant-stats strong small { font-size: 12px; }
.status-value { display: flex !important; align-items: center; gap: 9px; font-size: 18px !important; }
.status-value i { width: 9px; height: 9px; border-radius: 50%; background: var(--danger); }.status-value i.ready { background: var(--success); }
.selected-issue { padding: 24px; display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
.selected-issue h2 { margin: 8px 0 0; font-size: 20px; }.selected-issue p:last-child { margin: 8px 0 0; color: var(--muted); font-size: 13px; line-height: 1.7; }
.selected-issue > span, .rail-heading > span { padding: 7px 10px; border-radius: 999px; background: var(--soft); color: var(--primary); font-size: 11px; font-weight: 800; }
.rail-card { padding: 24px; }
dl { margin: 18px 0 0; display: grid; gap: 15px; } dl div { display: flex; justify-content: space-between; gap: 14px; } dt { color: var(--muted); font-size: 12px; } dd { margin: 0; max-width: 180px; overflow: hidden; font-size: 12px; font-weight: 800; text-align: right; text-overflow: ellipsis; white-space: nowrap; }
.rail-copy { margin: 15px 0 0; color: var(--muted); font-size: 12px; line-height: 1.8; }
.rail-heading { display: flex; align-items: center; justify-content: space-between; }
.shortcut-list { margin-top: 15px; display: grid; gap: 8px; }
.shortcut-list button { padding: 12px 13px; display: grid; gap: 4px; border: 0; border-radius: 15px; background: var(--soft); color: var(--ink); text-align: left; cursor: pointer; }
.shortcut-list button.active { box-shadow: inset 0 0 0 2px var(--primary); }.shortcut-list span { color: var(--primary); font-size: 9px; font-weight: 800; letter-spacing: .12em; }.shortcut-list strong { overflow: hidden; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 1100px) { .assistant-layout { grid-template-columns: 1fr; } .context-rail { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 760px) { .assistant-title-card { flex-direction: column; } .assistant-stats, .context-rail { grid-template-columns: 1fr; } }
</style>
