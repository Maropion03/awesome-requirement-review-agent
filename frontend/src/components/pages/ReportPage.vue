<template>
  <div class="report-page">
    <div class="page-header">
      <div>
        <p class="eyebrow">PRD Review Report</p>
        <h1>评审报告</h1>
        <p class="subtitle">保留维度分析、问题证据和本地处理状态，方便快速进入对话闭环。</p>
      </div>
      <div class="header-meta">
        <span class="meta-pill">评分：{{ report.score || '--' }}/10</span>
        <span class="meta-pill">建议：{{ report.suggestion || '尚未生成' }}</span>
        <span class="meta-pill">问题数：{{ report.issues?.length || 0 }}</span>
      </div>
    </div>

    <div class="report-content">
      <section class="summary-grid">
        <article class="summary-card primary">
          <span class="label">综合结论</span>
          <strong>{{ report.suggestion || '尚未生成' }}</strong>
          <p>{{ report.summary || '完成评审后，这里会出现结论摘要。' }}</p>
        </article>
        <article class="summary-card">
          <span class="label">高优问题</span>
          <strong>{{ highIssueCount }}</strong>
          <p>需要立即明确负责人和修改口径的问题数量。</p>
        </article>
        <article class="summary-card">
          <span class="label">本地跟踪</span>
          <strong>{{ trackedIssueCount }}</strong>
          <p>当前报告中已具备本地状态管理和导出能力的问题数。</p>
        </article>
      </section>

      <ReportViewer
        :report="report"
        :issue-state="issueState"
        :selected-issue-id="selectedIssueId"
        @issue-select="$emit('issue-select', $event)"
        @issue-status-change="$emit('issue-status-change', $event)"
        @export-suggestions="$emit('export-suggestions')"
      />
    </div>
  </div>
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
})

defineEmits(['issue-select', 'issue-status-change', 'export-suggestions'])

const highIssueCount = computed(() => {
  return (props.report.issues || []).filter((issue) => issue.severity === 'HIGH').length
})

const trackedIssueCount = computed(() => Object.keys(props.issueState || {}).length)
</script>

<style scoped>
.report-page {
  padding: 88px 20px 20px 300px;
  background: #fef8f1;
  min-height: calc(100vh - 64px);
  display: grid;
  gap: 18px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
  flex-wrap: wrap;
}

.eyebrow,
.subtitle,
.meta-pill,
.summary-card,
.summary-card .label {
  font-family: 'Inter', sans-serif;
}

.eyebrow {
  margin: 0 0 4px;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

h1,
.summary-card strong {
  font-family: 'Satoshi', sans-serif;
}

h1 {
  margin: 0;
  font-weight: 600;
  font-size: 1.75rem;
  color: #1d1b17;
  letter-spacing: -0.02em;
}

.subtitle {
  color: #64748b;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 4px 0 0;
}

.header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-pill {
  border: 1px solid #d8e1ef;
  background: #ffffff;
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 0.6875rem;
  font-weight: 600;
  color: #4b5563;
}

.report-content {
  display: grid;
  gap: 18px;
}

.summary-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.summary-card {
  background: #ffffff;
  border: 1px solid #dbe3ef;
  border-radius: 1rem;
  padding: 16px;
  display: grid;
  gap: 8px;
}

.summary-card.primary {
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.summary-card .label {
  color: #64748b;
  font-size: 0.75rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-weight: 600;
}

.summary-card strong {
  font-size: 1.45rem;
  color: #0f172a;
}

.summary-card p {
  margin: 0;
  color: #64748b;
  line-height: 1.5;
  font-size: 0.875rem;
}

@media (max-width: 1180px) {
  .report-page {
    padding-left: 20px;
    padding-top: 88px;
  }
}
</style>
