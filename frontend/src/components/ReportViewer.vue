<template>
  <div class="report-viewer">
    <section class="report-hero">
      <article class="score-panel">
        <p class="section-kicker">Total score</p>
        <div class="score-ring" :style="{ '--score-offset': scoreOffset }">
          <svg viewBox="0 0 128 128" aria-hidden="true">
            <circle class="ring-track" cx="64" cy="64" r="54" />
            <circle class="ring-value" cx="64" cy="64" r="54" />
          </svg>
          <div class="score-value">
            <strong>{{ report.score }}</strong>
            <span>/ 100</span>
          </div>
        </div>
        <p class="score-caption">基于六个评审维度加权计算的产品需求质量得分</p>
      </article>

      <article class="summary-panel">
        <div class="summary-heading">
          <div>
            <p class="section-kicker">Review conclusion</p>
            <h2>结论摘要</h2>
          </div>
          <span class="recommendation" :class="recommendationTone">{{ report.suggestion }}</span>
        </div>

        <p class="summary-copy">{{ report.summary || '评审完成后，这里会显示综合结论。' }}</p>

        <div class="summary-foot">
          <span><i class="summary-mark">✦</i> 六维并行评审</span>
          <span><i class="summary-mark verified">✓</i> 证据引用已校验</span>
          <span v-if="degradedCount" class="degraded-note">{{ degradedCount }} 个维度降级</span>
        </div>
      </article>
    </section>

    <section v-if="dimensionCards.length" class="dimension-section" aria-labelledby="dimension-title">
      <div class="section-title-row">
        <div>
          <p class="section-kicker">Dimension breakdown</p>
          <h2 id="dimension-title">各维度评分</h2>
        </div>
        <span>{{ dimensionCards.length }} 项</span>
      </div>

      <div class="dimension-strip">
        <details
          v-for="dimension in dimensionCards"
          :key="dimension.dimension"
          class="dimension-card"
          :class="dimension.statusTone"
        >
          <summary>
            <div class="dimension-score-row">
              <span class="dimension-icon" aria-hidden="true">{{ dimensionGlyph(dimension.dimension) }}</span>
              <strong>{{ dimension.score }}</strong>
              <small>/10</small>
            </div>
            <h3>{{ dimension.dimension }}</h3>
            <p>{{ dimension.summary }}</p>
            <span class="dimension-status">{{ dimension.statusLabel }}</span>
          </summary>
          <div class="dimension-detail">
            <p>{{ dimension.reasoning }}</p>
            <span>{{ dimension.issuesCount }} 个问题 · 权重 {{ dimension.weightLabel }}</span>
          </div>
        </details>
      </div>
    </section>

    <section class="issues-section" aria-labelledby="issues-title">
      <header class="issues-heading">
        <div>
          <p class="section-kicker">Detailed issues</p>
          <h2 id="issues-title">详细问题</h2>
        </div>
        <div class="issue-counts" aria-label="问题严重程度统计">
          <span v-for="count in severityCounts" :key="count.severity" :class="count.severity.toLowerCase()">
            <i></i>{{ count.label }}：{{ count.count }}
          </span>
          <button type="button" @click="$emit('export-suggestions')">导出修改建议</button>
        </div>
      </header>

      <div v-if="issues.length" class="issues-list">
        <article
          v-for="issue in issues"
          :key="issueIdentifier(issue)"
          class="issue-card"
          :class="[
            `severity-${issue.severity.toLowerCase()}`,
            { selected: issueIdentifier(issue) === selectedIssueId },
          ]"
        >
          <div class="issue-main">
            <div class="issue-overline">
              <span class="issue-id">{{ issue.displayId }}</span>
              <span v-if="issue.sourceSection || issue.sourceLocator" class="issue-location">
                {{ issue.sourceSection || issue.sourceLocator }}
              </span>
            </div>
            <h3>{{ issue.title }}</h3>
            <p class="issue-description">{{ issue.description }}</p>
          </div>

          <span class="severity-badge" :class="issue.severity.toLowerCase()">{{ issue.level }}</span>

          <div class="issue-suggestion">
            <strong>建议修改</strong>
            <p>{{ issue.suggestion }}</p>
          </div>

          <blockquote v-if="issue.sourceQuote" class="evidence-quote">
            <span>原文依据</span>
            “{{ issue.sourceQuote }}”
          </blockquote>

          <footer class="issue-footer">
            <div class="issue-tags">
              <span>{{ issue.dimension }}</span>
              <span>{{ readIssueStatusLabel(issue) }}</span>
            </div>

            <div class="issue-actions">
              <div class="status-actions" aria-label="处理状态">
                <button
                  v-for="option in statusOptions"
                  :key="option.value"
                  type="button"
                  :class="{ active: readIssueStatus(issue) === option.value }"
                  @click="updateStatus(issue, option.value)"
                >
                  {{ option.label }}
                </button>
              </div>
              <button class="ask-button" type="button" @click="$emit('issue-select', issue)">
                询问助手 →
              </button>
            </div>
          </footer>
        </article>
      </div>

      <div v-else class="empty-state">
        <strong>没有需要处理的问题</strong>
        <p>当前报告未返回问题项，仍可结合维度评分检查原始评审结论。</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import { getIssueIdentifier, getIssueStatus } from '../lib/issueState.js'

const props = defineProps({
  report: {
    type: Object,
    default: () => ({
      score: '--',
      suggestion: '尚未生成',
      summary: '评审完成后，这里会显示综合结论。',
      dimensionScores: [],
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
})

const emit = defineEmits(['issue-select', 'issue-status-change', 'export-suggestions'])

const statusOptions = [
  { value: 'todo', label: '待处理' },
  { value: 'accepted', label: '已采纳' },
  { value: 'ignored', label: '已忽略' },
  { value: 'fixed_pending_verify', label: '待复核' },
]

const statusLabels = Object.fromEntries(statusOptions.map((option) => [option.value, option.label]))
const ringCircumference = 2 * Math.PI * 54

const scoreNumber = computed(() => {
  const value = Number(props.report.score)
  return Number.isFinite(value) ? Math.min(100, Math.max(0, value)) : 0
})

const scoreOffset = computed(() => `${ringCircumference - (scoreNumber.value / 100) * ringCircumference}`)
const dimensionCards = computed(() => props.report.dimensionScores || [])
const issues = computed(() => props.report.issues || [])
const degradedCount = computed(() => props.report.rawReport?.degraded_dimensions?.length || 0)

const recommendationTone = computed(() => {
  const value = String(props.report.suggestion || '')
  if (value.includes('不通过') || value.includes('驳回')) return 'reject'
  if (value.includes('修改')) return 'modify'
  if (value.includes('通过')) return 'approve'
  return 'pending'
})

const severityCounts = computed(() => {
  const definitions = [
    { severity: 'HIGH', label: 'HIGH' },
    { severity: 'MEDIUM', label: 'MEDIUM' },
    { severity: 'LOW', label: 'LOW' },
  ]
  return definitions.map((definition) => ({
    ...definition,
    count: issues.value.filter((issue) => issue.severity === definition.severity).length,
  }))
})

function dimensionGlyph(name) {
  const glyphs = {
    需求完整性: '▣',
    需求合理性: '⌁',
    用户价值: '↗',
    技术可行性: '⚙',
    实现风险: '△',
    优先级一致性: '◎',
  }
  return glyphs[name] || '◆'
}

function issueIdentifier(issue) {
  return getIssueIdentifier(issue) || issue?.id || ''
}

function readIssueStatus(issue) {
  return getIssueStatus(props.issueState, issue)
}

function readIssueStatusLabel(issue) {
  return statusLabels[readIssueStatus(issue)] || '待处理'
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
  --primary: #3a2e47;
  --primary-soft: #51445f;
  --muted: #665f69;
  --surface: #fff;
  --soft: #f8f3ec;
  --line: #e6dfd7;
  width: min(1280px, 100%);
  margin: 0 auto;
  display: grid;
  gap: 40px;
}

.report-hero {
  display: grid;
  grid-template-columns: minmax(280px, 0.7fr) minmax(0, 1.6fr);
  gap: 28px;
}

.score-panel,
.summary-panel {
  border: 1px solid rgba(230, 223, 215, 0.72);
  border-radius: 26px;
  background: var(--surface);
  box-shadow: 0 18px 46px rgba(31, 24, 23, 0.065);
}

.score-panel {
  min-height: 390px;
  padding: 28px 34px 34px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.score-panel::after {
  content: '';
  position: absolute;
  width: 180px;
  height: 180px;
  right: -80px;
  top: -80px;
  border-radius: 50%;
  background: rgba(58, 46, 71, 0.05);
  filter: blur(12px);
}

.section-kicker {
  margin: 0;
  color: #948b95;
  font-size: 0.64rem;
  font-weight: 800;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}

.score-panel .section-kicker {
  align-self: flex-start;
}

.score-ring {
  width: 190px;
  height: 190px;
  margin: 24px 0 22px;
  position: relative;
}

.score-ring svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.score-ring circle {
  fill: none;
  stroke-width: 8;
}

.ring-track {
  stroke: #ede7e0;
}

.ring-value {
  stroke: var(--primary);
  stroke-dasharray: 339.292;
  stroke-dashoffset: var(--score-offset);
  stroke-linecap: round;
  transition: stroke-dashoffset 600ms cubic-bezier(.2, .8, .2, 1);
}

.score-value {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  justify-items: center;
}

.score-value strong {
  color: var(--primary);
  font-size: 3.55rem;
  font-weight: 780;
  letter-spacing: -0.07em;
  line-height: 1;
}

.score-value span {
  margin-top: 8px;
  color: var(--primary);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.score-caption {
  max-width: 250px;
  margin: 0;
  color: #514b53;
  font-size: 0.85rem;
  line-height: 1.75;
  text-align: center;
}

.summary-panel {
  min-height: 390px;
  padding: 48px 52px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.summary-heading {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 24px;
}

h2,
h3,
p {
  margin-top: 0;
}

.summary-heading h2,
.section-title-row h2,
.issues-heading h2 {
  margin: 8px 0 0;
  color: var(--primary);
  font-size: 1.35rem;
  letter-spacing: -0.025em;
}

.recommendation {
  padding: 10px 22px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 800;
  white-space: nowrap;
}

.recommendation.approve { background: #dff3e8; color: #256f4b; }
.recommendation.modify { background: #ffddb0; color: #614000; }
.recommendation.reject { background: #ffdad6; color: #93000a; }
.recommendation.pending { background: #ede7e0; color: #514b53; }

.summary-copy {
  max-width: 820px;
  margin: 28px 0 36px;
  color: #454047;
  font-size: 1rem;
  line-height: 2;
}

.summary-foot {
  padding-top: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 20px 28px;
  border-top: 1px solid var(--line);
  color: #29252b;
  font-size: 0.77rem;
  font-weight: 750;
}

.summary-foot span {
  display: inline-flex;
  align-items: center;
  gap: 9px;
}

.summary-mark {
  width: 22px;
  height: 22px;
  display: inline-grid;
  place-items: center;
  border-radius: 50%;
  background: #654300;
  color: #fff;
  font-style: normal;
}

.summary-mark.verified {
  background: var(--primary);
}

.summary-foot .degraded-note {
  margin-left: auto;
  color: #93000a;
}

.dimension-section,
.issues-section {
  display: grid;
  gap: 24px;
}

.section-title-row,
.issues-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 20px;
}

.section-title-row > span {
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 700;
}

.dimension-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(150px, 1fr));
  gap: 14px;
}

.dimension-card {
  min-width: 0;
  border: 1px solid rgba(230, 223, 215, 0.76);
  border-radius: 22px;
  background: #f8f3ec;
  overflow: hidden;
}

.dimension-card.danger { background: #fff7f6; }
.dimension-card.warning { background: #fff9ee; }
.dimension-card.good { background: #f1f9f4; }

.dimension-card summary {
  min-height: 220px;
  padding: 24px 22px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  list-style: none;
}

.dimension-card summary::-webkit-details-marker { display: none; }

.dimension-score-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  color: var(--primary);
}

.dimension-icon {
  width: 38px;
  height: 38px;
  margin-right: 5px;
  display: inline-grid;
  place-items: center;
  border-radius: 10px;
  background: rgba(58, 46, 71, 0.07);
  font-size: 1.05rem;
}

.dimension-score-row strong {
  font-size: 1.55rem;
  letter-spacing: -0.04em;
}

.dimension-score-row small {
  color: #827a83;
  font-size: 0.68rem;
  font-weight: 750;
}

.dimension-card h3 {
  margin: 24px 0 10px;
  color: var(--primary);
  font-size: 0.92rem;
}

.dimension-card summary p {
  margin: 0 0 18px;
  color: #665f69;
  display: -webkit-box;
  overflow: hidden;
  font-size: 0.74rem;
  line-height: 1.7;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.dimension-status {
  margin-top: auto;
  align-self: flex-start;
  color: #665f69;
  font-size: 0.67rem;
  font-weight: 800;
}

.dimension-detail {
  padding: 0 22px 22px;
  color: #514b53;
  font-size: 0.73rem;
  line-height: 1.7;
}

.dimension-detail p {
  margin: 0 0 10px;
}

.dimension-detail span {
  color: #827a83;
  font-weight: 750;
}

.issues-heading h2 {
  font-size: 2rem;
}

.issue-counts {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 9px;
}

.issue-counts > span,
.issue-counts > button {
  min-height: 40px;
  padding: 0 15px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid transparent;
  border-radius: 11px;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.issue-counts i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.issue-counts .high { background: #fff0ed; color: #a61616; }
.issue-counts .high i { background: #d96c6c; }
.issue-counts .medium { background: #fff0d7; color: #5c3600; }
.issue-counts .medium i { background: #654300; }
.issue-counts .low { background: #ece8e3; color: #514b53; }
.issue-counts .low i { background: #756a7c; }

.issue-counts > button {
  border-color: var(--line);
  background: #fff;
  color: var(--primary);
  cursor: pointer;
  letter-spacing: 0;
}

.issues-list {
  display: grid;
  gap: 18px;
}

.issue-card {
  padding: 28px 30px 24px 34px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px 28px;
  border: 1px solid rgba(230, 223, 215, 0.78);
  border-left: 4px solid #756a7c;
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 16px 38px rgba(31, 24, 23, 0.055);
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.issue-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 20px 44px rgba(31, 24, 23, 0.085);
}

.issue-card.selected {
  box-shadow: 0 0 0 3px rgba(58, 46, 71, 0.14), 0 20px 44px rgba(31, 24, 23, 0.085);
}

.issue-card.severity-high { border-left-color: #c62020; }
.issue-card.severity-medium { border-left-color: #d58a18; }
.issue-card.severity-low { border-left-color: #756a7c; }

.issue-overline {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 0.72rem;
}

.issue-id {
  color: #b61e1e;
  font-weight: 850;
}

.issue-location {
  color: #918991;
}

.issue-location::before {
  content: '•';
  margin-right: 10px;
}

.issue-main h3 {
  margin: 10px 0 12px;
  color: var(--primary);
  font-size: 1.18rem;
  letter-spacing: -0.015em;
}

.issue-description,
.issue-suggestion p,
.evidence-quote {
  color: #514b53;
  font-size: 0.88rem;
  line-height: 1.85;
}

.issue-description {
  margin: 0;
}

.severity-badge {
  min-width: 70px;
  height: 30px;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 0.64rem;
  font-weight: 850;
  letter-spacing: 0.12em;
}

.severity-badge.high { background: #ffd9d5; color: #9d1515; }
.severity-badge.medium { background: #ffe7bd; color: #654300; }
.severity-badge.low { background: #ece8e3; color: #514b53; }

.issue-suggestion,
.evidence-quote,
.issue-footer {
  grid-column: 1 / -1;
}

.issue-suggestion {
  padding: 18px 20px;
  display: grid;
  gap: 6px;
  border-radius: 14px;
  background: #f8f3ec;
}

.issue-suggestion strong,
.evidence-quote span {
  color: var(--primary);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.issue-suggestion p {
  margin: 0;
}

.evidence-quote {
  margin: 0;
  padding: 0 0 0 18px;
  border-left: 2px solid #d1c0e1;
  font-style: normal;
}

.evidence-quote span {
  display: block;
  margin-bottom: 5px;
}

.issue-footer {
  padding-top: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-top: 1px solid var(--line);
}

.issue-tags,
.issue-actions,
.status-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.issue-tags span {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f8f3ec;
  color: #665f69;
  font-size: 0.68rem;
  font-weight: 700;
}

.status-actions button,
.ask-button {
  border: 0;
  background: transparent;
  color: #8b838c;
  cursor: pointer;
  font-size: 0.69rem;
  font-weight: 700;
}

.status-actions button {
  padding: 6px 7px;
  border-radius: 7px;
}

.status-actions button.active {
  background: var(--primary);
  color: #fff;
}

.ask-button {
  padding: 8px 11px;
  color: var(--primary);
}

.empty-state {
  padding: 56px 24px;
  border: 1px dashed #d1c8be;
  border-radius: 22px;
  color: #665f69;
  text-align: center;
}

.empty-state strong {
  color: var(--primary);
  font-size: 1.1rem;
}

.empty-state p {
  margin: 8px 0 0;
}

@media (max-width: 1120px) {
  .dimension-strip {
    grid-template-columns: repeat(3, minmax(180px, 1fr));
  }
}

@media (max-width: 860px) {
  .report-hero {
    grid-template-columns: 1fr;
  }

  .score-panel {
    min-height: 330px;
  }

  .summary-panel {
    min-height: 320px;
    padding: 36px 30px;
  }

  .dimension-strip {
    grid-template-columns: repeat(2, minmax(160px, 1fr));
  }

  .issues-heading,
  .issue-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 560px) {
  .summary-heading,
  .section-title-row,
  .issues-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .dimension-strip {
    grid-template-columns: 1fr;
  }

  .dimension-card summary {
    min-height: 190px;
  }

  .issue-card {
    padding: 24px 20px;
  }

  .severity-badge {
    grid-column: 1;
    grid-row: 2;
    justify-self: start;
  }
}
</style>
