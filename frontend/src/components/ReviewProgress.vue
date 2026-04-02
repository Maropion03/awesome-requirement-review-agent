<template>
  <section class="card progress-card">
    <div class="section-head">
      <div>
        <h2>评审进度</h2>
        <p class="desc">跟踪当前 Agent 链路、维度完成状态和流式回传信息。</p>
      </div>
      <span class="progress-pill">{{ progress }}%</span>
    </div>

    <div v-if="agentStages.length" class="stage-grid">
      <article
        v-for="stage in agentStages"
        :key="stage.id"
        class="stage-card"
        :class="stage.status"
      >
        <div class="stage-top">
          <strong>{{ stage.title }}</strong>
          <span class="stage-status">{{ stageStatusLabel(stage.status) }}</span>
        </div>
        <p class="stage-description">{{ stage.description }}</p>
        <p class="stage-detail">{{ stage.detail }}</p>
      </article>
    </div>

    <div class="progress-wrap">
      <div class="progress-label">维度完成度 {{ progress }}%</div>
      <div class="progress-bg">
        <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
      </div>
    </div>

    <ul class="dimension-list">
      <li v-for="item in dimensions" :key="item.id" :class="item.status">
        <span>{{ item.name }}</span>
        <span class="status-pill" :class="item.status">{{ dimensionStatusLabel(item.status) }}</span>
      </li>
    </ul>

    <div class="stream-box">
      <h3>流式输出</h3>
      <pre>{{ streamText || '等待开始...' }}</pre>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  agentStages: {
    type: Array,
    default: () => [],
  },
  dimensions: {
    type: Array,
    default: () => [],
  },
  streamText: {
    type: String,
    default: '',
  },
})

const progress = computed(() => {
  if (!props.dimensions.length) return 0
  const done = props.dimensions.filter((item) => item.status === 'complete').length
  return Math.round((done / props.dimensions.length) * 100)
})

function dimensionStatusLabel(status) {
  const map = {
    pending: '等待中',
    active: '进行中',
    complete: '已完成',
  }

  return map[status] || status
}

function stageStatusLabel(status) {
  const map = {
    pending: '待命',
    active: '执行中',
    complete: '完成',
    error: '异常',
  }

  return map[status] || status
}
</script>

<style scoped>
.card {
  background: #ffffff;
  border: 1px solid transparent;
  border-radius: 1rem;
  padding: 16px;
  box-shadow: 0 4px 6px rgba(31, 24, 23, 0.06);
}

.progress-card {
  display: grid;
  gap: 16px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

h2,
h3,
p {
  margin: 0;
}

h2 {
  font-family: 'Satoshi', sans-serif;
  font-size: 1.125rem;
  color: #1d1b17;
}

.desc,
.progress-label,
.stage-description,
.stage-detail,
.status-pill,
.stage-status,
pre {
  font-family: 'Inter', sans-serif;
}

.desc {
  margin-top: 4px;
  color: #64748b;
  font-size: 0.875rem;
  line-height: 1.5;
}

.progress-pill {
  border-radius: 999px;
  background: #f3eef8;
  color: #4b2f68;
  padding: 7px 12px;
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  font-weight: 600;
}

.stage-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.stage-card {
  border: 1px solid #d8e1ef;
  border-radius: 1rem;
  background: #fbfdff;
  padding: 14px;
  display: grid;
  gap: 6px;
}

.stage-card.active {
  border-color: #93c5fd;
  background: #eff6ff;
}

.stage-card.complete {
  border-color: #86efac;
  background: #f0fdf4;
}

.stage-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

.stage-top strong {
  color: #0f172a;
  font-family: 'Satoshi', sans-serif;
}

.stage-status {
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.stage-description {
  color: #475569;
  font-size: 0.8125rem;
  line-height: 1.5;
}

.stage-detail {
  color: #0f172a;
  font-size: 0.8125rem;
  font-weight: 600;
}

.progress-wrap {
  display: grid;
  gap: 8px;
}

.progress-label {
  color: #334155;
  font-weight: 600;
}

.progress-bg {
  height: 10px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(to right, #3a2e47, #51445f);
  transition: width 0.3s ease;
}

.dimension-list {
  padding: 0;
  list-style: none;
  margin: 0;
  display: grid;
  gap: 8px;
}

.dimension-list li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 0.85rem;
  background: #fafafa;
  border: 1px solid #edf2f7;
  font-family: 'Inter', sans-serif;
  color: #1f2937;
}

.status-pill {
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-pill.pending {
  background: #f8fafc;
  color: #64748b;
}

.status-pill.active {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-pill.complete {
  background: #dcfce7;
  color: #166534;
}

.stream-box {
  border-top: 1px solid #edf2f7;
  padding-top: 12px;
  display: grid;
  gap: 8px;
}

h3 {
  font-family: 'Satoshi', sans-serif;
  font-size: 1rem;
  color: #1d1b17;
}

pre {
  background: #111827;
  color: #eff6ff;
  border-radius: 1rem;
  min-height: 120px;
  padding: 14px;
  white-space: pre-wrap;
  margin: 0;
  line-height: 1.6;
  font-size: 0.8125rem;
}

@media (max-width: 720px) {
  .section-head {
    flex-direction: column;
  }
}
</style>
