<template>
  <main class="workbench-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Open-source · BYOK · Stateless</p>
        <h1>把 PRD 放上评审台</h1>
        <p class="subtitle">六个维度并行审查，证据、评分和修改建议一次返回。</p>
      </div>
      <div class="header-meta">
        <span>文件 / {{ selectedFileName || '未选择' }}</span>
        <span>模型 / {{ providerName }} · {{ apiConfig.model }}</span>
      </div>
    </header>

    <section class="workbench-flow">
      <UploadArea
        v-model="selectedFileNameModel"
        :status="uploadState"
        :error-message="uploadError"
        :disabled="isRunning"
        @file-selected="$emit('file-selected', $event)"
        @clear-file="$emit('clear-file')"
      />

      <ConfigPanel
        :model-value="apiConfig"
        :providers="providers"
        @update:model-value="$emit('update:api-config', $event)"
      />

      <section class="launch-row">
        <div class="step-mark">03</div>
        <div class="launch-copy">
          <strong>{{ isRunning ? '评审正在运行' : '启动评审' }}</strong>
          <span>{{ launchHint }}</span>
        </div>
        <button class="reset-button" type="button" :disabled="isRunning" @click="$emit('reset-demo')">重置结果</button>
        <button class="launch-button" type="button" :disabled="!canStart" @click="$emit('start-review')">
          {{ isRunning ? '正在分析…' : '开始六维评审 →' }}
        </button>
      </section>

      <ReviewProgress
        :agent-stages="agentStages"
        :dimensions="dimensions"
        :stream-text="streamText"
      />
    </section>
  </main>
</template>

<script setup>
import { computed } from 'vue'
import UploadArea from '../UploadArea.vue'
import ConfigPanel from '../ConfigPanel.vue'
import ReviewProgress from '../ReviewProgress.vue'

const props = defineProps({
  selectedFileName: { type: String, default: '' },
  uploadState: { type: String, default: 'idle' },
  uploadError: { type: String, default: '' },
  isRunning: Boolean,
  apiConfig: { type: Object, required: true },
  providers: { type: Array, default: () => [] },
  streamText: { type: String, default: '' },
  agentStages: { type: Array, default: () => [] },
  dimensions: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'update:selected-file-name',
  'update:api-config',
  'file-selected',
  'clear-file',
  'start-review',
  'reset-demo',
])

const selectedFileNameModel = computed({
  get: () => props.selectedFileName,
  set: (value) => emit('update:selected-file-name', value),
})

const providerName = computed(() => props.providers.find((item) => item.id === props.apiConfig.provider)?.name || props.apiConfig.provider)
const canStart = computed(() => Boolean(
  !props.isRunning &&
  props.selectedFileName &&
  props.apiConfig.apiKey?.trim() &&
  props.apiConfig.model?.trim(),
))
const launchHint = computed(() => {
  if (props.isRunning) return '请保持此页面打开；结果会按维度实时返回。'
  if (!props.selectedFileName) return '先选择一份 .md 或 .docx 文档。'
  if (!props.apiConfig.apiKey?.trim()) return '填写 API Key 后即可开始。'
  return '本次运行不会创建服务器会话，也不会保存文档或 Key。'
})
</script>

<style scoped>
.workbench-page {
  min-height: calc(100vh - 64px);
  padding: 96px 28px 40px 300px;
  background:
    linear-gradient(rgba(32, 29, 23, .04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(32, 29, 23, .04) 1px, transparent 1px),
    #f6f0e5;
  background-size: 28px 28px;
}

.page-header {
  max-width: 1180px;
  margin: 0 auto 24px;
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 24px;
}

.eyebrow { margin: 0 0 6px; color: #ff5a1f; font: 800 11px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: .12em; text-transform: uppercase; }
h1 { margin: 0; color: #1f1d19; font: 750 clamp(32px, 4vw, 54px)/1.02 'Avenir Next', 'PingFang SC', sans-serif; letter-spacing: -.045em; }
.subtitle { margin: 10px 0 0; color: #6e675c; font-size: 14px; }
.header-meta { display: grid; gap: 6px; color: #5f594f; font: 11px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; text-align: right; }

.workbench-flow { max-width: 1180px; margin: 0 auto; display: grid; gap: 16px; }
.launch-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border: 1px solid #1f1d19;
  border-radius: 18px;
  background: #fffdf8;
}
.step-mark { width: 42px; height: 42px; flex: 0 0 42px; display: grid; place-items: center; border-radius: 50%; background: #ff5a1f; color: #fff; font: 700 13px/1 ui-monospace, SFMono-Regular, Menlo, monospace; }
.launch-copy { display: grid; gap: 3px; min-width: 0; }
.launch-copy strong { font-size: 15px; }
.launch-copy span { color: #716b60; font-size: 12px; }
.reset-button,
.launch-button { border-radius: 11px; padding: 12px 16px; font-weight: 750; cursor: pointer; }
.reset-button { margin-left: auto; border: 1px solid #bcb4a7; background: #fff; color: #39352e; }
.launch-button { border: 1px solid #1f1d19; background: #1f1d19; color: #fff; min-width: 170px; }
.launch-button:hover:not(:disabled) { background: #ff5a1f; border-color: #ff5a1f; }
.reset-button:disabled,
.launch-button:disabled { opacity: .42; cursor: not-allowed; }

@media (max-width: 1180px) {
  .workbench-page { padding-left: 24px; }
}
@media (max-width: 700px) {
  .workbench-page { padding: 120px 14px 28px; }
  .page-header { align-items: start; flex-direction: column; }
  .header-meta { text-align: left; }
  .launch-row { flex-wrap: wrap; }
  .reset-button { margin-left: 0; }
  .launch-button { width: 100%; }
}
</style>
