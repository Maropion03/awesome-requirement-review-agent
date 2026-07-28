<template>
  <div class="report-viewer">
    <section class="report-overview">
      <article class="score-summary surface-card">
        <p class="overline">Total score</p>
        <div class="score-body">
          <div class="score-ring" :style="{ '--score-progress': `${scoreNumber * 3.6}deg` }">
            <div><strong>{{ report.score }}</strong><span>/ 100</span></div>
          </div>
          <div class="recommendation-block">
            <p class="overline">Recommendation</p>
            <span class="recommendation">{{ report.suggestion }}</span>
            <p class="overline summary-label">Summary</p>
            <p class="summary-copy">{{ report.summary || '暂无摘要。' }}</p>
          </div>
        </div>
      </article>

      <div class="analysis-grid">
        <article class="radar-card surface-card">
          <p class="overline">Radar</p>
          <RadarChart :dimensions="dimensionCards" />
        </article>
        <article class="dimensions-card surface-card">
          <header><p class="overline">Dimensions</p><strong>{{ dimensionCards.length }} 项</strong></header>
          <div class="dimension-grid">
            <div v-for="dimension in dimensionCards" :key="dimension.dimension" class="dimension-tile">
              <span>{{ dimensionGlyph(dimension.dimension) }}</span>
              <strong>{{ dimension.score }}<small>/10</small></strong>
              <p>{{ dimension.dimension }}</p>
              <small>{{ dimension.issuesCount }} 个问题</small>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section class="issues-section surface-card" aria-labelledby="issues-title">
      <header class="issues-heading">
        <div><p class="overline">Issues</p><h2 id="issues-title">详细问题</h2></div>
        <div class="issue-counts">
          <span v-for="count in severityCounts" :key="count.severity" :class="count.severity.toLowerCase()">{{ count.label }} · {{ count.count }}</span>
          <button type="button" @click="$emit('export-suggestions')">导出修改建议</button>
        </div>
      </header>

      <div v-if="issues.length" class="issues-list">
        <article
          v-for="issue in issues"
          :key="issueIdentifier(issue)"
          class="issue-card"
          :class="[`severity-${issue.severity.toLowerCase()}`, { selected: issueIdentifier(issue) === selectedIssueId }]"
        >
          <div class="issue-copy">
            <div class="issue-meta"><span>{{ issue.displayId }}</span><span>{{ issue.dimension }}</span><span v-if="issue.sourceSection || issue.sourceLocator">{{ issue.sourceSection || issue.sourceLocator }}</span></div>
            <h3>{{ issue.title }}</h3>
            <p>{{ issue.description }}</p>
            <blockquote v-if="issue.sourceQuote"><strong>原文依据</strong>“{{ issue.sourceQuote }}”</blockquote>
            <div class="suggestion"><strong>建议修改</strong><p>{{ issue.suggestion }}</p></div>
          </div>
          <aside class="issue-side">
            <span class="severity-badge">{{ issue.level }}</span>
            <div class="status-actions">
              <button v-for="option in statusOptions" :key="option.value" type="button" :class="{ active: readIssueStatus(issue) === option.value }" @click="updateStatus(issue, option.value)">{{ option.label }}</button>
            </div>
            <button class="ask-button" type="button" @click="$emit('issue-select', issue)">询问助手 →</button>
          </aside>
        </article>
      </div>
      <div v-else class="empty-state"><strong>没有需要处理的问题</strong><p>当前报告未返回问题项。</p></div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import RadarChart from './RadarChart.vue'
import { getIssueIdentifier, getIssueStatus } from '../lib/issueState.js'

const props = defineProps({
  report: { type: Object, default: () => ({ score: '--', suggestion: '尚未生成', summary: '', dimensionScores: [], issues: [] }) },
  issueState: { type: Object, default: () => ({}) },
  selectedIssueId: { type: String, default: '' },
})
const emit = defineEmits(['issue-select', 'issue-status-change', 'export-suggestions'])
const statusOptions = [
  { value: 'todo', label: '待处理' }, { value: 'accepted', label: '已采纳' },
  { value: 'ignored', label: '已忽略' }, { value: 'fixed_pending_verify', label: '待复核' },
]
const scoreNumber = computed(() => Math.min(100, Math.max(0, Number(props.report.score) || 0)))
const dimensionCards = computed(() => props.report.dimensionScores || [])
const issues = computed(() => props.report.issues || [])
const severityCounts = computed(() => ['HIGH', 'MEDIUM', 'LOW'].map((severity) => ({ severity, label: severity, count: issues.value.filter((issue) => issue.severity === severity).length })))
const glyphs = { 需求完整性: '▣', 需求合理性: '⌁', 用户价值: '↗', 技术可行性: '⚙', 实现风险: '△', 优先级一致性: '◎' }
function dimensionGlyph(name) { return glyphs[name] || '◆' }
function issueIdentifier(issue) { return getIssueIdentifier(issue) || issue?.id || '' }
function readIssueStatus(issue) { return getIssueStatus(props.issueState, issue) }
function updateStatus(issue, status) { emit('issue-status-change', { issue, issueId: issueIdentifier(issue), status }) }
</script>

<style scoped>
.report-viewer { display: grid; gap: 24px; }
.report-overview { display: grid; grid-template-columns: minmax(390px, .82fr) minmax(0, 1.18fr); gap: 24px; }
.score-summary { padding: 30px; }
.score-body { min-height: 300px; display: grid; grid-template-columns: 170px 1fr; align-items: center; gap: 28px; }
.score-ring { width: 158px; height: 158px; display: grid; place-items: center; border-radius: 50%; background: conic-gradient(var(--primary) var(--score-progress), var(--soft) 0); position: relative; }
.score-ring::after { content: ''; position: absolute; inset: 12px; border-radius: 50%; background: var(--panel); }
.score-ring div { z-index: 1; display: grid; text-align: center; }
.score-ring strong { color: var(--primary); font-size: 46px; line-height: 1; }
.score-ring span { margin-top: 6px; color: var(--muted); font-size: 11px; font-weight: 700; letter-spacing: .2em; }
.recommendation { display: inline-flex; margin-top: 10px; padding: 9px 14px; border-radius: 999px; background: var(--soft); color: var(--primary); font-weight: 800; }
.summary-label { margin-top: 26px; }
.summary-copy { margin: 9px 0 0; color: var(--muted); font-size: 13px; line-height: 1.8; }
.analysis-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.radar-card, .dimensions-card { min-width: 0; padding: 24px; }
.dimensions-card header { display: flex; justify-content: space-between; color: var(--primary); }
.dimension-grid { margin-top: 18px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.dimension-tile { min-width: 0; padding: 14px; border-radius: 18px; background: var(--soft); }
.dimension-tile > span { color: var(--primary); }
.dimension-tile strong { margin-left: 8px; color: var(--primary); font-size: 20px; }
.dimension-tile strong small { font-size: 10px; }
.dimension-tile p { margin: 8px 0 3px; overflow: hidden; font-size: 12px; font-weight: 800; text-overflow: ellipsis; white-space: nowrap; }
.dimension-tile > small { color: var(--muted); font-size: 10px; }
.issues-section { padding: 26px; }
.issues-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; }
h2 { margin: 8px 0 0; font-size: 26px; }
.issue-counts { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.issue-counts span, .issue-counts button { padding: 7px 11px; border: 0; border-radius: 999px; background: var(--soft); color: var(--muted); font-size: 11px; font-weight: 800; }
.issue-counts .high { color: var(--danger); }.issue-counts .medium { color: var(--primary); }.issue-counts button { cursor: pointer; color: var(--primary); }
.issues-list { margin-top: 22px; display: grid; gap: 14px; }
.issue-card { padding: 22px 22px 20px 26px; display: grid; grid-template-columns: minmax(0, 1fr) 210px; gap: 24px; border: 1px solid var(--line); border-left: 5px solid var(--line); border-radius: 25px; background: #fffdf8; }
.issue-card.severity-high { border-left-color: var(--danger); }.issue-card.severity-medium { border-left-color: var(--primary); }.issue-card.selected { box-shadow: 0 0 0 3px rgb(239 108 0 / 13%); }
.issue-meta { display: flex; flex-wrap: wrap; gap: 8px; color: var(--muted); font-size: 10px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
.issue-meta span { padding: 5px 8px; border-radius: 999px; background: var(--soft); }
.issue-card h3 { margin: 13px 0 7px; font-size: 19px; }
.issue-copy > p { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.75; }
blockquote { margin: 15px 0 0; padding: 13px 15px; border: 0; border-radius: 15px; background: #fff3e3; color: var(--muted); font-size: 12px; line-height: 1.7; }
blockquote strong { display: block; color: var(--primary); }
.suggestion { margin-top: 14px; padding: 14px 16px; border-radius: 16px; background: var(--soft); }
.suggestion strong { color: var(--primary); font-size: 11px; }.suggestion p { margin: 5px 0 0; color: var(--ink); font-size: 12px; line-height: 1.7; }
.issue-side { display: flex; align-items: flex-end; flex-direction: column; gap: 14px; }
.severity-badge { padding: 7px 10px; border-radius: 999px; background: #fff0e7; color: var(--danger); font-size: 11px; font-weight: 800; }
.status-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; width: 100%; }
.status-actions button, .ask-button { min-height: 34px; border: 0; border-radius: 999px; background: var(--soft); color: var(--muted); cursor: pointer; font-size: 11px; font-weight: 700; }
.status-actions button.active { background: var(--ink); color: #fff; }.ask-button { width: 100%; background: var(--primary); color: #fff; }
.empty-state { padding: 70px 20px; text-align: center; }.empty-state p { color: var(--muted); }
@media (max-width: 1180px) { .report-overview { grid-template-columns: 1fr; } }
@media (max-width: 760px) { .score-body, .analysis-grid, .issue-card { grid-template-columns: 1fr; } .issues-heading { align-items: flex-start; flex-direction: column; } .issue-counts { justify-content: flex-start; } .issue-side { align-items: stretch; } }
</style>
