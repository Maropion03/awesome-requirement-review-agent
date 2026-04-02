<template>
  <div class="workbench-page">
    <div class="page-header">
      <div>
        <p class="eyebrow">PRD Review Workbench</p>
        <h1>PRD 评审工作台</h1>
        <p class="subtitle">上传文档、配置评审并监控进度</p>
      </div>
      <div class="header-meta">
        <span class="meta-pill">当前文件：{{ selectedFileName || '未选择' }}</span>
        <span class="meta-pill">preset：{{ preset }}</span>
      </div>
    </div>

    <div class="workbench-content">
      <section class="workbench-section">
        <UploadArea
          v-model="selectedFileName"
          :status="uploadState"
          :error-message="uploadError"
          :disabled="isRunning"
          @file-selected="onFileSelected"
          @clear-file="clearSelectedFile"
        />

        <ConfigPanel v-model="preset" />

        <section class="card action-row">
          <button class="primary" :disabled="isRunning" @click="startReview">开始评审</button>
          <button :disabled="isRunning" @click="resetDemo">重置</button>
          <span class="tip">配置完成后，点击开始评审按钮启动多维度分析</span>
        </section>

        <ReviewProgress
          :agent-stages="agentStages"
          :dimensions="dimensions"
          :stream-text="streamText"
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, defineProps, defineEmits, ref, watch } from 'vue'
import UploadArea from '../UploadArea.vue'
import ConfigPanel from '../ConfigPanel.vue'
import ReviewProgress from '../ReviewProgress.vue'
import {
  createAgentStages,
  applyDimensionEvent,
  applyStreamingMessage,
  completeReporterStage,
} from '../../lib/agentStages.js'
import { createBaseDimensions } from '../../lib/reviewApi.js'

// Props and emits
const props = defineProps({
  selectedFileName: String,
  uploadState: String,
  uploadError: String,
  isRunning: Boolean,
  preset: String,
  streamText: String,
  agentStages: Array,
  dimensions: Array,
})

const emit = defineEmits([
  'update:selectedFileName',
  'update:uploadState', 
  'update:uploadError',
  'update:isRunning',
  'update:preset',
  'update:streamText',
  'update:agentStages',
  'update:dimensions',
  'file-selected',
  'clear-file',
  'start-review',
  'reset-demo'
])

// Local refs (these will mirror props for local manipulation)
const selectedFileName = computed({
  get: () => props.selectedFileName,
  set: (value) => emit('update:selectedFileName', value)
})

const uploadState = computed({
  get: () => props.uploadState,
  set: (value) => emit('update:uploadState', value)
})

const uploadError = computed({
  get: () => props.uploadError,
  set: (value) => emit('update:uploadError', value)
})

const isRunning = computed({
  get: () => props.isRunning,
  set: (value) => emit('update:isRunning', value)
})

const preset = computed({
  get: () => props.preset,
  set: (value) => emit('update:preset', value)
})

const streamText = computed({
  get: () => props.streamText,
  set: (value) => emit('update:streamText', value)
})

const agentStages = computed({
  get: () => props.agentStages,
  set: (value) => emit('update:agentStages', value)
})

const dimensions = computed({
  get: () => props.dimensions,
  set: (value) => emit('update:dimensions', value)
})

// Methods
const onFileSelected = (file) => {
  emit('file-selected', file)
}

const clearSelectedFile = () => {
  emit('clear-file')
}

const startReview = () => {
  emit('start-review')
}

const resetDemo = () => {
  emit('reset-demo')
}

// Initialize if needed
if (!agentStages.value || agentStages.value.length === 0) {
  emit('update:agentStages', createAgentStages())
}

if (!dimensions.value || dimensions.value.length === 0) {
  emit('update:dimensions', createBaseDimensions())
}
</script>

<style scoped>
.workbench-page {
  padding: 88px 20px 20px 300px; /* Account for fixed header (64px) and sidebar (280px) */
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

.eyebrow {
  margin: 0 0 4px;
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

h1 {
  margin: 0;
  font-family: 'Satoshi', sans-serif;
  font-weight: 600;
  font-size: 1.75rem;
  color: #1d1b17;
  letter-spacing: -0.02em;
}

.subtitle,
.tip,
.meta-pill {
  font-family: 'Inter', sans-serif;
  color: #64748b;
  font-size: 0.875rem;
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
  font-weight: 500;
}

.workbench-content {
  display: grid;
  gap: 18px;
}

.workbench-section {
  display: grid;
  gap: 12px;
}

.card {
  background: #ffffff;
  border: 1px solid transparent;
  border-radius: 1rem;
  padding: 16px;
  box-shadow: 0 4px 6px rgba(31, 24, 23, 0.06);
}

.action-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

button {
  border: 1px solid #cbd5e1;
  background: #ffffff;
  border-radius: 1rem;
  padding: 8px 14px;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 0.875rem;
}

button.primary {
  background: linear-gradient(to right, #3a2e47, #51445f);
  color: #ffffff;
  border-color: #3a2e47;
}

button:hover:enabled {
  filter: brightness(0.98);
}

button:active:enabled {
  transform: translateY(1px);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 1180px) {
  .workbench-page {
    padding-left: 20px;
    padding-top: 88px;
  }
}
</style>
