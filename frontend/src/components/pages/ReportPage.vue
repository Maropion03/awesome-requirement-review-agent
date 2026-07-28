<template>
  <main class="report-page">
    <header class="report-heading">
      <div>
        <p class="eyebrow">PRD Review Report</p>
        <h1>评审报告<span v-if="projectName">：{{ projectName }}</span></h1>
        <p class="report-meta">{{ reportMeta }}</p>
      </div>

      <div class="report-actions" aria-label="报告操作">
        <button class="action-button" type="button" @click="$emit('export-suggestions')">
          <span aria-hidden="true">↓</span>
          导出建议
        </button>
        <button
          class="action-button"
          type="button"
          :disabled="!canOpenAssistant"
          @click="$emit('open-assistant')"
        >
          <span aria-hidden="true">✦</span>
          进入助手
        </button>
        <button class="action-button primary" type="button" @click="$emit('rerun')">
          <span aria-hidden="true">↻</span>
          重新评审
        </button>
      </div>
    </header>

    <ReportViewer
      :report="report"
      :issue-state="issueState"
      :selected-issue-id="selectedIssueId"
      @issue-select="$emit('issue-select', $event)"
      @issue-status-change="$emit('issue-status-change', $event)"
      @export-suggestions="$emit('export-suggestions')"
    />
  </main>
</template>

<script setup>
import { computed } from 'vue'

import ReportViewer from '../ReportViewer.vue'

const props = defineProps({
  report: {
    type: Object,
    default: () => ({
      score: '--',
      suggestion: '尚未生成',
      summary: '完成评审后，这里会出现结论摘要。',
      issues: [],
      rawReport: null,
    }),
  },
  issueState: {
    type: Object,
    default: () => ({}),
  },
  selectedIssueId: {
    type: String,
    default: '',
  },
  canOpenAssistant: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'issue-select',
  'issue-status-change',
  'export-suggestions',
  'open-assistant',
  'rerun',
])

const projectName = computed(() => props.report.rawReport?.project_name || '')

const reportMeta = computed(() => {
  const raw = props.report.rawReport || {}
  const date = raw.review_date || '本次评审'
  const preset = raw.preset || 'normal'
  return `${date} · ${preset} 模式 · ${props.report.issues?.length || 0} 个问题`
})
</script>

<style scoped>
.report-page {
  --report-primary: #3a2e47;
  --report-muted: #665f69;
  --report-surface: #fff;
  --report-line: #e6dfd7;
  min-height: calc(100vh - 64px);
  padding: 104px 32px 72px 312px;
  background: #fef8f1;
  color: #1d1b17;
}

.report-heading {
  width: min(1280px, 100%);
  margin: 0 auto 36px;
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #978f98;
  font-size: 0.6875rem;
  font-weight: 750;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: var(--report-primary);
  font-family: 'Avenir Next', 'PingFang SC', sans-serif;
  font-size: clamp(1.8rem, 3vw, 2.35rem);
  font-weight: 750;
  letter-spacing: -0.035em;
}

.report-meta {
  margin: 8px 0 0;
  color: var(--report-muted);
  font-size: 0.8125rem;
}

.report-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.action-button {
  min-height: 42px;
  padding: 0 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--report-line);
  border-radius: 999px;
  background: var(--report-surface);
  color: var(--report-primary);
  box-shadow: 0 10px 28px rgba(31, 24, 23, 0.06);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 700;
  transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
}

.action-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 14px 32px rgba(31, 24, 23, 0.1);
}

.action-button.primary {
  border-color: var(--report-primary);
  background: var(--report-primary);
  color: #fff;
}

.action-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

@media (max-width: 1180px) {
  .report-page {
    padding-left: 28px;
  }
}

@media (max-width: 760px) {
  .report-page {
    padding: 92px 18px 52px;
  }

  .report-heading {
    align-items: start;
    flex-direction: column;
  }

  .report-actions {
    width: 100%;
    justify-content: stretch;
  }

  .action-button {
    flex: 1 1 130px;
  }
}
</style>
