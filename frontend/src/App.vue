<template>
  <main class="page">
    <h1>PRD 评审低保真流程 Demo</h1>

    <UploadArea v-model="selectedFileName" />

    <ConfigPanel v-model="preset" />

    <section class="card action-row">
      <button class="primary" :disabled="isRunning" @click="startReview">开始评审</button>
      <button :disabled="isRunning" @click="resetDemo">重置</button>
      <span class="tip">当前文件：{{ selectedFileName || '未选择' }} | preset：{{ preset }}</span>
    </section>

    <ReviewProgress :dimensions="dimensions" :stream-text="streamText" />

    <ReportViewer :report="report" />
  </main>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import UploadArea from './components/UploadArea.vue'
import ConfigPanel from './components/ConfigPanel.vue'
import ReviewProgress from './components/ReviewProgress.vue'
import ReportViewer from './components/ReportViewer.vue'

const selectedFileName = ref('')
const preset = ref('normal')
const isRunning = ref(false)
const streamText = ref('')
const tick = ref(0)
let timer = null

const baseDimensions = [
  { id: 1, name: '需求完整性', status: 'pending' },
  { id: 2, name: '需求合理性', status: 'pending' },
  { id: 3, name: '用户价值', status: 'pending' },
  { id: 4, name: '技术可行性', status: 'pending' },
  { id: 5, name: '实现风险', status: 'pending' },
  { id: 6, name: '优先级一致性', status: 'pending' }
]

const dimensions = ref(baseDimensions.map((d) => ({ ...d })))

const report = ref({
  score: '--',
  suggestion: '尚未生成',
  issues: []
})

const mockStreamLines = [
  '读取文档结构并提取目标...',
  '正在校验验收标准与边界条件...',
  '发现 1 个高优先级缺口：验收条件不完整。',
  '正在评估用户价值与优先级一致性...',
  '风险项补充建议已生成。',
  '全部维度完成，准备输出报告。'
]

function startReview() {
  if (isRunning.value) return

  resetProgressOnly()
  isRunning.value = true

  // 预留：后续接入 API 时可在此触发请求
  // e.g. await api.startReview({ file: selectedFileName.value, preset: preset.value })

  timer = setInterval(() => {
    const index = tick.value

    if (index > 0) {
      onProgressEvent(index - 1, 'complete')
    }

    if (index < dimensions.value.length) {
      onProgressEvent(index, 'active')
      streamText.value += `${mockStreamLines[index]}\n`
      tick.value += 1
      return
    }

    clearInterval(timer)
    timer = null
    onCompleteEvent()
  }, 900)
}

function onProgressEvent(index, status) {
  if (!dimensions.value[index]) return
  dimensions.value[index].status = status
}

function onCompleteEvent() {
  isRunning.value = false
  report.value = {
    score: '8.7',
    suggestion: '修改后通过',
    issues: [
      { id: 'H-1', level: '高', title: '验收标准缺失边界用例' },
      { id: 'M-1', level: '中', title: '技术依赖未明确负责人' },
      { id: 'M-2', level: '中', title: '优先级说明可再量化' }
    ]
  }
}

function resetProgressOnly() {
  tick.value = 0
  streamText.value = ''
  report.value = { score: '--', suggestion: '尚未生成', issues: [] }
  dimensions.value = baseDimensions.map((d) => ({ ...d }))
}

function resetDemo() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  isRunning.value = false
  resetProgressOnly()
}

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.page {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px;
  display: grid;
  gap: 12px;
  background: #f8fafc;
  min-height: 100vh;
}

h1 {
  margin: 0;
  font-size: 24px;
}

.card {
  background: #fff;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  padding: 16px;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

button {
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 6px;
  padding: 8px 14px;
  cursor: pointer;
}

button.primary {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

button:hover:enabled {
  filter: brightness(0.97);
}

button:active:enabled {
  transform: translateY(1px);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tip {
  color: #64748b;
  font-size: 14px;
}
</style>
