<template>
  <main class="page-shell report-page">
    <PageHeader
      title="评审报告"
      description="查看总分、六维评分和详细问题，并从任一问题进入追问。"
      :can-view-report="true"
      :can-open-assistant="canOpenAssistant"
      @navigate="$emit('navigate', $event)"
    />

    <section class="report-title-card surface-card">
      <div>
        <p class="overline">Report</p>
        <h1>评审报告<span v-if="projectName"> · {{ projectName }}</span></h1>
        <p>{{ reportMeta }}</p>
      </div>
      <div class="title-actions">
        <button class="pill-button" type="button" @click="$emit('navigate', 'workbench')">返回工作台</button>
        <button class="pill-button" type="button" @click="$emit('export-suggestions')">导出 MD</button>
        <button class="pill-button primary" type="button" :disabled="!canOpenAssistant" @click="$emit('open-assistant')">打开助手</button>
      </div>
    </section>

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
import PageHeader from '../layout/PageHeader.vue'

const props = defineProps({
  report: { type: Object, default: () => ({ score: '--', suggestion: '尚未生成', summary: '', issues: [] }) },
  issueState: { type: Object, default: () => ({}) },
  selectedIssueId: { type: String, default: '' },
  canOpenAssistant: Boolean,
})

defineEmits(['issue-select', 'issue-status-change', 'export-suggestions', 'open-assistant', 'rerun', 'navigate'])
const projectName = computed(() => props.report.rawReport?.project_name || '')
const reportMeta = computed(() => {
  const raw = props.report.rawReport || {}
  return `${raw.version || 'v1.0'} · ${raw.review_date || '本次评审'} · ${raw.preset || 'normal'} 模式 · ${props.report.issues?.length || 0} 个问题`
})
</script>

<style scoped>
.report-title-card { margin-bottom: 24px; padding: 24px 26px; display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
h1 { margin: 8px 0 0; font-size: 30px; letter-spacing: -.03em; }
.report-title-card p:last-child { margin: 8px 0 0; color: var(--muted); font-size: 13px; }
.title-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 10px; }
@media (max-width: 760px) { .report-title-card { flex-direction: column; } .title-actions { width: 100%; justify-content: flex-start; } }
</style>
