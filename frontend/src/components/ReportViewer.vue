<template>
  <div class="report-viewer">
    <section class="card viewer-header">
      <div>
        <h2>评审报告</h2>
        <p class="subtitle">{{ report.summary || '评审完成后，这里会显示综合结论。' }}</p>
      </div>

      <div class="summary-row">
        <div class="summary-item">
          <span class="label">综合评分</span>
          <strong>{{ report.score }}/10</strong>
        </div>
        <div class="summary-item">
          <span class="label">评审建议</span>
          <strong>{{ report.suggestion }}</strong>
        </div>
        <div class="summary-item">
          <span class="label">问题总数</span>
          <strong>{{ totalIssues }}</strong>
        </div>
      </div>
    </section>

    <section v-if="dimensionCards.length" class="dimension-grid">
      <article
        v-for="dimension in dimensionCards"
        :key="dimension.dimension"
        class="dimension-card"
        :class="dimension.statusTone"
      >
        <button class="dimension-toggle" type="button" @click="toggleDimension(dimension.dimension)">
          <div>
            <p class="dimension-name">{{ dimension.dimension }}</p>
            <strong>{{ dimension.score }}/10</strong>
          </div>
          <span class="dimension-status">{{ dimension.statusLabel }}</span>
        </button>

        <div class="dimension-body" :class="{ expanded: isExpanded(dimension.dimension) }">
          <div class="dimension-copy">
            <h4>评分说明</h4>
            <p>{{ dimension.reasoning }}</p>
          </div>

          <div class="dimension-copy">
            <h4>主要问题</h4>
            <ul>
              <li v-for="issue in dimension.topIssues" :key="issue.id">{{ issue.title }}</li>
              <li v-if="!dimension.topIssues.length">当前维度未发现需要重点追踪的问题。</li>
            </ul>
          </div>

          <div class="dimension-copy">
            <h4>修改方向</h4>
            <ul>
              <li v-for="hint in dimension.actionHints" :key="hint">{{ hint }}</li>
            </ul>
          </div>
        </div>
      </article>
    </section>

    <section class="card issues-shell">
      <div class="section-head">
        <div>
          <h3>问题清单</h3>
          <p class="section-copy">每条问题都保留证据链、本地处理状态和导出能力。</p>
        </div>
        <button class="primary-action" type="button" @click="$emit('export-suggestions')">
          导出修改建议
        </button>
      </div>

      <div v-if="issueGroups.length" class="issue-groups">
        <section v-for="group in issueGroups" :key="group.severity" class="issue-group">
          <header class="group-header">
            <h4>{{ group.label }}</h4>
            <span>{{ group.count }} 条</span>
          </header>

          <article
            v-for="issue in group.issues"
            :key="issue.id"
            class="issue-card"
            :class="[
              `severity-${issue.severity.toLowerCase()}`,
              { selected: issueIdentifier(issue) === selectedIssueId },
            ]"
          >
            <div class="issue-top">
              <div class="issue-pills">
                <span class="issue-pill strong">{{ issue.displayId }}</span>
                <span class="issue-pill">{{ issue.level }}优先级</span>
                <span class="issue-pill">{{ issue.dimension }}</span>
              </div>
              <button class="link-button" type="button" @click="emitIssueSelection(issue)">
                聚焦到助手
              </button>
            </div>

            <h5>{{ issue.title }}</h5>
            <p class="issue-description">{{ issue.description }}</p>
            <p class="issue-suggestion">
              <strong>修改建议</strong>
              <span>{{ issue.suggestion }}</span>
            </p>

            <div
              v-if="issue.sourceQuote || issue.sourceSection || issue.sourceLocator"
              class="issue-evidence"
            >
              <div class="evidence-head">
                <span>原文依据</span>
                <button class="link-button small" type="button" @click="emitIssueSelection(issue)">
                  查看上下文
                </button>
              </div>
              <p v-if="issue.sourceQuote" class="source-quote">“{{ issue.sourceQuote }}”</p>
              <div class="source-meta">
                <span v-if="issue.sourceSection">{{ issue.sourceSection }}</span>
                <span v-if="issue.sourceLocator">{{ issue.sourceLocator }}</span>
              </div>
            </div>

            <div class="status-row">
              <span class="status-label">处理状态</span>
              <div class="status-actions">
                <button
                  v-for="option in statusOptions"
                  :key="option.value"
                  class="status-button"
                  :class="{ active: readIssueStatus(issue) === option.value }"
                  type="button"
                  @click="updateStatus(issue, option.value)"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
          </article>
        </section>
      </div>

      <div v-else class="empty-state">
        <p>评审完成后，这里会展示维度结论、证据链和修改建议。</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

import { getIssueIdentifier, getIssueStatus } from '../lib/issueState.js'
import { isDimensionExpanded, toggleDimensionExpansion } from '../lib/reportDimensions.js'

const props = defineProps({
  report: {
    type: Object,
    default: () => ({
      score: '--',
      suggestion: '尚未生成',
      summary: '评审完成后，这里会显示综合结论。',
      dimensionScores: [],
      issueGroups: [],
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

const emit = defineEmits(['issue-select', 'issue-status-change', 'export-suggestions'])

const expandedDimensions = ref([])
const statusOptions = [
  { value: 'todo', label: '待处理' },
  { value: 'accepted', label: '已采纳' },
  { value: 'ignored', label: '已忽略' },
  { value: 'fixed_pending_verify', label: '待复核' },
]

const dimensionCards = computed(() => props.report.dimensionScores || [])
const issueGroups = computed(() => props.report.issueGroups || [])
const totalIssues = computed(() => props.report.issues?.length || 0)

function issueIdentifier(issue) {
  return getIssueIdentifier(issue) || issue?.id || ''
}

function toggleDimension(name) {
  expandedDimensions.value = toggleDimensionExpansion(expandedDimensions.value, name)
}

function isExpanded(name) {
  return isDimensionExpanded(expandedDimensions.value, name)
}

function emitIssueSelection(issue) {
  emit('issue-select', issue)
}

function readIssueStatus(issue) {
  return getIssueStatus(props.issueState, issue)
}

function updateStatus(issue, status) {
  emit('issue-status-change', {
    issue,
    issueId: issueIdentifier(issue),
    status,
  })
}
</script>

<style scoped>
.report-viewer {
  display: grid;
  gap: 18px;
}

.card {
  background: #ffffff;
  border: 1px solid #dbe3ef;
  border-radius: 1.25rem;
  padding: 18px;
  box-shadow: 0 4px 6px rgba(31, 24, 23, 0.06);
}

.viewer-header,
.section-head,
.issue-top,
.evidence-head,
.status-row,
.group-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

h2,
h3,
h4,
h5,
p,
ul {
  margin: 0;
}

h2,
h3,
h4,
h5,
.dimension-name,
.summary-item strong {
  font-family: 'Satoshi', sans-serif;
}

.subtitle,
.section-copy,
.summary-item .label,
.summary-item strong,
.dimension-status,
.dimension-copy,
.issue-card,
.status-button,
.link-button,
.primary-action {
  font-family: 'Inter', sans-serif;
}

h2 {
  color: #1d1b17;
  font-size: 1.2rem;
}

h3 {
  color: #1d1b17;
  font-size: 1.05rem;
}

.subtitle,
.section-copy {
  margin-top: 6px;
  color: #64748b;
  font-size: 0.875rem;
  line-height: 1.5;
}

.summary-row {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  min-width: min(100%, 420px);
}

.summary-item {
  padding: 14px;
  border-radius: 1rem;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  border: 1px solid #d8e1ef;
  display: grid;
  gap: 6px;
}

.summary-item .label {
  color: #64748b;
  font-size: 0.75rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.summary-item strong {
  color: #0f172a;
  font-size: 1.35rem;
}

.dimension-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.dimension-card {
  border-radius: 1.15rem;
  border: 1px solid #dbe3ef;
  padding: 16px;
  background: #ffffff;
  display: grid;
  gap: 14px;
}

.dimension-card.warning {
  background: #fffbeb;
}

.dimension-card.danger {
  background: #fef7f7;
}

.dimension-card.good {
  background: #f0fdf4;
}

.dimension-toggle {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.dimension-name {
  margin-bottom: 4px;
  color: #1d1b17;
  font-size: 0.95rem;
}

.dimension-toggle strong {
  color: #0f172a;
  font-size: 1.25rem;
}

.dimension-status {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #d8e1ef;
  color: #475569;
  padding: 7px 11px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.dimension-body {
  display: grid;
  gap: 12px;
}

.dimension-body.expanded {
  gap: 14px;
}

.dimension-copy {
  display: grid;
  gap: 8px;
}

.dimension-copy h4 {
  color: #334155;
  font-size: 0.9rem;
}

.dimension-copy p,
.dimension-copy li {
  color: #475569;
  line-height: 1.6;
  font-size: 0.875rem;
}

.dimension-copy ul {
  padding-left: 18px;
  display: grid;
  gap: 4px;
}

.issues-shell {
  display: grid;
  gap: 16px;
}

.primary-action,
.link-button,
.status-button {
  border-radius: 999px;
  cursor: pointer;
}

.primary-action {
  border: 1px solid #3a2e47;
  background: linear-gradient(to right, #3a2e47, #51445f);
  color: #ffffff;
  padding: 10px 14px;
  font-size: 0.875rem;
  font-weight: 600;
}

.issue-groups {
  display: grid;
  gap: 18px;
}

.issue-group {
  display: grid;
  gap: 12px;
}

.group-header {
  align-items: center;
}

.group-header h4 {
  font-size: 0.95rem;
  color: #1d1b17;
}

.group-header span {
  color: #64748b;
  font-family: 'Inter', sans-serif;
  font-size: 0.8125rem;
}

.issue-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 1rem;
  border: 1px solid #dbe3ef;
  background: #fcfdff;
}

.issue-card.selected {
  border-color: #7c93c7;
  box-shadow: 0 0 0 2px rgba(124, 147, 199, 0.12);
}

.issue-card.severity-high {
  border-left: 4px solid #dc2626;
}

.issue-card.severity-medium {
  border-left: 4px solid #f59e0b;
}

.issue-card.severity-low {
  border-left: 4px solid #10b981;
}

.issue-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.issue-pill {
  border-radius: 999px;
  background: #f8fafc;
  color: #475569;
  border: 1px solid #dbe3ef;
  padding: 6px 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

.issue-pill.strong {
  background: #eef4ff;
  color: #243b6b;
}

.link-button {
  border: 1px solid #d8e1ef;
  background: #ffffff;
  color: #334155;
  padding: 8px 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.link-button.small {
  padding: 6px 10px;
}

h5 {
  color: #111827;
  font-size: 1rem;
}

.issue-description,
.issue-suggestion,
.source-quote,
.source-meta,
.status-label {
  color: #475569;
  font-size: 0.875rem;
  line-height: 1.6;
}

.issue-suggestion {
  display: grid;
  gap: 4px;
}

.issue-suggestion strong {
  color: #111827;
}

.issue-evidence {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 1rem;
  background: #f8fbff;
  border: 1px solid #d5e4fb;
}

.evidence-head span {
  color: #243b6b;
  font-size: 0.8125rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.source-quote {
  color: #243b6b;
  font-weight: 600;
}

.source-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.source-meta span {
  border-radius: 999px;
  background: #ffffff;
  border: 1px solid #dbe3ef;
  padding: 5px 9px;
}

.status-row {
  align-items: center;
}

.status-label {
  font-weight: 600;
}

.status-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-button {
  border: 1px solid #d8e1ef;
  background: #ffffff;
  color: #334155;
  padding: 7px 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-button.active {
  background: #3a2e47;
  border-color: #3a2e47;
  color: #ffffff;
}

.empty-state {
  padding: 28px 16px;
  border-radius: 1rem;
  background: #f8fafc;
  border: 1px dashed #d8e1ef;
  color: #64748b;
  font-family: 'Inter', sans-serif;
  text-align: center;
}

@media (max-width: 960px) {
  .summary-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .viewer-header,
  .section-head,
  .issue-top,
  .status-row {
    flex-direction: column;
  }

  .primary-action,
  .link-button {
    width: fit-content;
  }
}
</style>
