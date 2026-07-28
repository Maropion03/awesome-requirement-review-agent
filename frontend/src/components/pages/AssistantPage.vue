<template>
  <main class="assistant-page">
    <header class="assistant-heading">
      <div>
        <p class="eyebrow">Review assistant</p>
        <h1>报告摘要与评审助手</h1>
        <p>AI 助手会带着当前报告和选中的问题继续回答，刷新页面后上下文自动清除。</p>
      </div>
      <button class="back-button" type="button" @click="$emit('back-to-report')">← 返回报告</button>
    </header>

    <section class="assistant-stats" aria-label="助手上下文摘要">
      <article>
        <span>综合评分</span>
        <strong>{{ report.score }}<small>/100</small></strong>
      </article>
      <article>
        <span>评审建议</span>
        <strong class="recommendation">{{ report.suggestion }}</strong>
      </article>
      <article>
        <span>连接状态</span>
        <strong class="status-value">
          <i :class="{ ready: canChat }"></i>{{ canChat ? '请求就绪' : '缺少 Key' }}
        </strong>
      </article>
      <article>
        <span>当前模型</span>
        <strong class="model-value">{{ providerLabel || '尚未配置' }}</strong>
      </article>
    </section>

    <div class="assistant-layout">
      <AssistantPanel
        class="conversation-panel"
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

      <aside class="context-rail" aria-label="报告上下文与快捷操作">
        <section class="rail-section workflow-actions">
          <p class="rail-label">Workflow</p>
          <button type="button" @click="$emit('back-to-report')">
            <span aria-hidden="true">←</span>
            <span><strong>查看完整报告</strong><small>返回维度和问题详情</small></span>
          </button>
          <button type="button" @click="$emit('run-action', { type: 'generate_suggestion', label: '生成修改建议' })">
            <span aria-hidden="true">✦</span>
            <span><strong>生成修改建议</strong><small>基于当前问题给出修改稿</small></span>
          </button>
          <button type="button" @click="$emit('export-suggestions')">
            <span aria-hidden="true">↓</span>
            <span><strong>导出建议</strong><small>下载本地 Markdown 文件</small></span>
          </button>
          <button type="button" @click="$emit('rerun')">
            <span aria-hidden="true">↻</span>
            <span><strong>重新评审</strong><small>返回工作台确认后重跑</small></span>
          </button>
        </section>

        <section class="rail-section selected-context">
          <div class="rail-heading">
            <p class="rail-label">Selected issue</p>
            <span v-if="selectedIssue">{{ selectedIssue.displayId || selectedIssue.id }}</span>
          </div>
          <template v-if="selectedIssue">
            <h2>{{ selectedIssue.title }}</h2>
            <p>{{ selectedIssue.description }}</p>
            <button
              type="button"
              @click="$emit('send-message', `请详细解释 ${selectedIssue.displayId || selectedIssue.id}，并给出可直接替换的修改稿`)"
            >
              围绕此问题提问 →
            </button>
          </template>
          <p v-else>从报告页选择问题后，这里会展示对应上下文。</p>
        </section>

        <section class="rail-section report-summary">
          <p class="rail-label">Report summary</p>
          <p>{{ report.summary }}</p>
        </section>

        <section class="rail-section issue-shortcuts">
          <div class="rail-heading">
            <p class="rail-label">Issue shortcuts</p>
            <span>{{ issues.length }}</span>
          </div>
          <div v-if="issues.length" class="shortcut-list">
            <button
              v-for="issue in issues.slice(0, 6)"
              :key="issue.issueKey || issue.displayId || issue.id"
              type="button"
              :class="{ active: isSelected(issue) }"
              @click="$emit('select-issue', issue.issueKey || issue.displayId || issue.id)"
            >
              <span>{{ issue.displayId || issue.id }}</span>
              <strong>{{ issue.title }}</strong>
            </button>
          </div>
          <p v-else>当前报告没有问题快捷入口。</p>
        </section>
      </aside>
    </div>
  </main>
</template>

<script setup>
import { computed } from 'vue'

import AssistantPanel from '../AssistantPanel.vue'

const props = defineProps({
  report: {
    type: Object,
    default: () => ({ score: '--', suggestion: '尚未生成', summary: '', issues: [] }),
  },
  canChat: Boolean,
  providerLabel: String,
  chatMessages: {
    type: Array,
    default: () => [],
  },
  selectedIssue: Object,
  assistantSuggestedActions: {
    type: Array,
    default: () => [],
  },
  assistantSourceRefs: {
    type: Array,
    default: () => [],
  },
  assistantStatus: String,
  assistantResponseMode: String,
  isChatLoading: Boolean,
  assistantSnapshot: Object,
})

defineEmits([
  'send-message',
  'run-action',
  'select-issue',
  'back-to-report',
  'export-suggestions',
  'rerun',
])

const issues = computed(() => props.report.issues || [])

function isSelected(issue) {
  if (!props.selectedIssue) return false
  const selectedIds = [props.selectedIssue.issueKey, props.selectedIssue.displayId, props.selectedIssue.id]
  return [issue.issueKey, issue.displayId, issue.id].some((id) => id && selectedIds.includes(id))
}
</script>

<style scoped>
.assistant-page {
  --primary: #3a2e47;
  --primary-soft: #51445f;
  --muted: #665974;
  --surface: #fff;
  --soft: #f8f3ec;
  --line: #e4ddd5;
  min-height: 100vh;
  padding: 98px 28px 28px 312px;
  background: #fef8f1;
  color: #1d1b17;
}

.assistant-heading {
  width: min(1320px, 100%);
  margin: 0 auto 24px;
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
}

.eyebrow,
.rail-label {
  margin: 0 0 8px;
  color: #978f98;
  font-size: 0.64rem;
  font-weight: 800;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: var(--primary);
  font-size: clamp(1.8rem, 3vw, 2.25rem);
  letter-spacing: -0.035em;
}

.assistant-heading p:last-child {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 0.88rem;
  line-height: 1.65;
}

.back-button {
  min-height: 42px;
  padding: 0 17px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fff;
  color: var(--primary);
  cursor: pointer;
  font-weight: 750;
  box-shadow: 0 10px 28px rgba(31, 24, 23, 0.06);
}

.assistant-stats {
  width: min(1320px, 100%);
  margin: 0 auto 20px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.assistant-stats article {
  min-height: 108px;
  padding: 18px 20px;
  display: grid;
  align-content: space-between;
  gap: 10px;
  border-bottom: 2px solid rgba(58, 46, 71, 0.07);
  border-radius: 16px;
  background: var(--soft);
}

.assistant-stats span {
  color: var(--muted);
  font-size: 0.63rem;
  font-weight: 800;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.assistant-stats strong {
  min-width: 0;
  color: var(--primary);
  font-size: 1.55rem;
  line-height: 1.15;
}

.assistant-stats small {
  margin-left: 5px;
  color: var(--muted);
  font-size: 0.72rem;
}

.assistant-stats .recommendation {
  font-size: 1rem;
}

.assistant-stats .status-value {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 1rem;
}

.status-value i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #d58a18;
}

.status-value i.ready {
  background: #2f8a5d;
}

.assistant-stats .model-value {
  overflow: hidden;
  font-size: 0.9rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.assistant-layout {
  width: min(1320px, 100%);
  min-height: 640px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
  align-items: stretch;
}

.conversation-panel {
  min-width: 0;
}

.context-rail {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 28px;
  border-left: 1px solid var(--line);
  background: var(--soft);
}

.rail-section {
  min-width: 0;
}

.rail-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.rail-heading > span {
  padding: 4px 8px;
  border-radius: 999px;
  background: #ede7e0;
  color: var(--primary);
  font-size: 0.66rem;
  font-weight: 800;
}

.workflow-actions {
  display: grid;
  gap: 9px;
}

.workflow-actions > button {
  width: 100%;
  padding: 13px 14px;
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 10px;
  border: 0;
  border-radius: 13px;
  background: #fff;
  color: var(--primary);
  cursor: pointer;
  text-align: left;
  box-shadow: 0 6px 18px rgba(31, 24, 23, 0.04);
}

.workflow-actions > button > span:first-child {
  font-size: 1rem;
  text-align: center;
}

.workflow-actions strong,
.workflow-actions small {
  display: block;
}

.workflow-actions strong {
  font-size: 0.78rem;
}

.workflow-actions small {
  margin-top: 3px;
  color: #8c848d;
  font-size: 0.64rem;
  font-weight: 500;
}

.selected-context,
.report-summary,
.issue-shortcuts {
  padding-top: 22px;
  border-top: 1px solid var(--line);
}

.selected-context h2 {
  margin: 10px 0 8px;
  color: var(--primary);
  font-size: 0.95rem;
  line-height: 1.45;
}

.selected-context > p,
.report-summary > p:last-child,
.issue-shortcuts > p:last-child {
  margin: 0;
  color: var(--muted);
  font-size: 0.75rem;
  line-height: 1.7;
}

.selected-context > button {
  margin-top: 12px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--primary);
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 800;
}

.shortcut-list {
  display: grid;
  gap: 8px;
}

.shortcut-list button {
  width: 100%;
  padding: 11px 12px;
  display: grid;
  gap: 4px;
  border: 1px solid transparent;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.7);
  color: var(--primary);
  cursor: pointer;
  text-align: left;
}

.shortcut-list button.active {
  border-color: #d1c0e1;
  background: #fff;
}

.shortcut-list span {
  color: #9a2830;
  font-size: 0.62rem;
  font-weight: 850;
}

.shortcut-list strong {
  overflow: hidden;
  font-size: 0.72rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1180px) {
  .assistant-page {
    padding-left: 28px;
  }
}

@media (max-width: 900px) {
  .assistant-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .assistant-layout {
    grid-template-columns: 1fr;
  }

  .context-rail {
    border-top: 1px solid var(--line);
    border-left: 0;
  }
}

@media (max-width: 620px) {
  .assistant-page {
    padding: 92px 16px 18px;
  }

  .assistant-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .assistant-stats {
    grid-template-columns: 1fr;
  }
}
</style>
