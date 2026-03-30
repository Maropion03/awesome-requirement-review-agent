<template>
  <div class="card">
    <h2>Step 3: 评审进度</h2>

    <div class="progress-wrap">
      <div class="progress-label">总进度 {{ progress }}%</div>
      <div class="progress-bg">
        <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
      </div>
    </div>

    <ul class="dimension-list">
      <li v-for="item in dimensions" :key="item.id" :class="item.status">
        <span>{{ item.name }}</span>
        <span class="status-pill">{{ statusLabel(item.status) }}</span>
      </li>
    </ul>

    <div class="stream-box">
      <h3>流式输出</h3>
      <pre>{{ streamText || '等待开始...' }}</pre>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  dimensions: {
    type: Array,
    default: () => []
  },
  streamText: {
    type: String,
    default: ''
  }
})

const progress = computed(() => {
  if (!props.dimensions.length) return 0
  const done = props.dimensions.filter((item) => item.status === 'complete').length
  return Math.round((done / props.dimensions.length) * 100)
})

function statusLabel(status) {
  const map = {
    pending: '⏳ pending',
    active: '🔄 active',
    complete: '✅ complete'
  }
  return map[status] || status
}
</script>

<style scoped>
.card {
  background: #fff;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  padding: 16px;
}

.progress-wrap {
  margin-bottom: 12px;
}

.progress-label {
  font-weight: 600;
  margin-bottom: 6px;
}

.progress-bg {
  height: 10px;
  border-radius: 999px;
  background: #e2e8f0;
}

.progress-bar {
  height: 100%;
  border-radius: 999px;
  background: #2563eb;
  transition: width 0.3s ease;
}

.dimension-list {
  padding: 0;
  list-style: none;
  margin: 0 0 16px;
}

.dimension-list li {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px dashed #e2e8f0;
}

.status-pill {
  font-size: 13px;
}

.stream-box {
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
}

h3 {
  margin: 0 0 8px;
  font-size: 16px;
}

pre {
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 6px;
  min-height: 90px;
  padding: 10px;
  white-space: pre-wrap;
  margin: 0;
}
</style>
