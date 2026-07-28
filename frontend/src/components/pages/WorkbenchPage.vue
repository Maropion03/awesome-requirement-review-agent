<template>
  <main class="page-shell workbench-page">
    <PageHeader
      title="新建 PRD 评审任务"
      description="上传 PRD，选择评审模式，直接在当前工作台观察 Agent 链路、查看报告并继续追问。"
      :can-view-report="canViewReport"
      :can-open-assistant="canOpenAssistant"
      @navigate="$emit('navigate', $event)"
    />

    <div class="workbench-grid">
      <div class="left-column">
        <section class="workbench-intro surface-card">
          <div>
            <p class="overline">Workbench</p>
            <h1>上传文档并启动评审</h1>
            <p>文档和用户 API Key 仅随本次无状态请求发送。报告与助手保留在当前页面会话内。</p>
          </div>
          <button class="api-state" type="button" @click="$emit('navigate', 'settings')">
            <span>{{ apiConfig.apiKey ? 'API 已配置' : '配置 API' }}</span>
            <small>{{ providerName }} · {{ apiConfig.model }}</small>
          </button>
        </section>

        <UploadArea
          v-model="selectedFileNameModel"
          :status="uploadState"
          :error-message="uploadError"
          :disabled="isRunning"
          @file-selected="$emit('file-selected', $event)"
          @clear-file="$emit('clear-file')"
        />

        <div class="configuration-grid">
          <section class="surface-card mode-card">
            <header><span aria-hidden="true">⌁</span><div><h2>评审预设</h2><p>选择后随评审请求发送。</p></div></header>
            <div class="preset-list">
              <button v-for="preset in presets" :key="preset.id" type="button" :class="{ active: apiConfig.preset === preset.id }" @click="selectPreset(preset.id)">
                <strong>{{ preset.label }}</strong><small>{{ preset.description }}</small>
              </button>
            </div>
          </section>

          <section class="surface-card agent-card">
            <header><span aria-hidden="true">✦</span><div><h2>协作 Agent</h2><p>六维流水线固定启用。</p></div></header>
            <div class="agent-list">
              <div v-for="agent in agents" :key="agent.name">
                <span><strong>{{ agent.name }}</strong><small>{{ agent.description }}</small></span>
                <i aria-label="已启用"><b></b></i>
              </div>
            </div>
          </section>
        </div>
      </div>

      <ReviewProgress
        :agent-stages="agentStages"
        :dimensions="dimensions"
        :stream-text="streamText"
        :is-running="isRunning"
        :can-start="canStart"
        :can-view-report="canViewReport"
        :can-open-assistant="canOpenAssistant"
        @start-review="$emit('start-review')"
        @reset="$emit('reset-demo')"
        @navigate="$emit('navigate', $event)"
      />
    </div>
  </main>
</template>

<script setup>
import { computed } from 'vue'
import PageHeader from '../layout/PageHeader.vue'
import ReviewProgress from '../ReviewProgress.vue'
import UploadArea from '../UploadArea.vue'

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
  canViewReport: Boolean,
  canOpenAssistant: Boolean,
})

const emit = defineEmits(['update:selected-file-name', 'update:api-config', 'file-selected', 'clear-file', 'start-review', 'reset-demo', 'navigate'])
const selectedFileNameModel = computed({ get: () => props.selectedFileName, set: (value) => emit('update:selected-file-name', value) })
const providerName = computed(() => props.providers.find((item) => item.id === props.apiConfig.provider)?.name || props.apiConfig.provider || '未配置')
const canStart = computed(() => Boolean(!props.isRunning && props.selectedFileName && props.apiConfig.apiKey?.trim() && props.apiConfig.model?.trim()))

const presets = [
  { id: 'normal', label: '标准模式', description: '覆盖完整业务逻辑与常规功能审查。' },
  { id: 'p0_critical', label: 'P0 紧急模式', description: '突出稳定性、可用性与核心链路风险。' },
  { id: 'innovation', label: '创新模式', description: '强调体验、差异化与用户价值评估。' },
]
const agents = [
  { name: '研发 Agent', description: '关注技术可行性与实现风险' },
  { name: '产品 Agent', description: '关注完整性、合理性和优先级' },
  { name: '用户 Agent', description: '关注用户价值与体验表达' },
]

function selectPreset(preset) { emit('update:api-config', { ...props.apiConfig, preset }) }
</script>

<style scoped>
.workbench-grid { display: grid; grid-template-columns: minmax(0,1.35fr) minmax(340px,.85fr); gap: 24px; align-items: start; }
.left-column { min-width: 0; display: grid; gap: 24px; }
.workbench-intro { padding: 24px; display: flex; align-items: start; justify-content: space-between; gap: 20px; }
h1 { margin: 8px 0 0; color: var(--ink); font-size: 24px; }
.workbench-intro p:last-child { max-width: 650px; margin: 8px 0 0; color: var(--muted); font-size: 13px; line-height: 1.8; }
.api-state { min-width: 190px; padding: 12px 14px; display: grid; gap: 5px; border: 1px solid var(--line); border-radius: 16px; background: var(--soft); color: var(--primary); cursor: pointer; text-align: left; }
.api-state span { font-weight: 800; } .api-state small { max-width: 210px; overflow: hidden; color: var(--muted); text-overflow: ellipsis; white-space: nowrap; }
.configuration-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 24px; }
.mode-card, .agent-card { padding: 24px; }
.mode-card header, .agent-card header { display: flex; align-items: center; gap: 12px; }
.mode-card header > span, .agent-card header > span { color: var(--primary); font-size: 24px; }
h2, header p { margin: 0; } h2 { font-size: 17px; } header p { margin-top: 4px; color: var(--muted); font-size: 12px; }
.preset-list, .agent-list { margin-top: 22px; display: grid; gap: 12px; }
.preset-list button, .agent-list > div { min-height: 68px; padding: 14px 16px; border: 1px solid var(--line); border-radius: 16px; background: var(--soft); color: var(--ink); text-align: left; }
.preset-list button { cursor: pointer; } .preset-list button.active { border-color: var(--primary); background: var(--panel); box-shadow: 0 10px 24px rgba(31,29,25,.08); }
.preset-list strong, .preset-list small, .agent-list strong, .agent-list small { display: block; }
.preset-list strong, .agent-list strong { font-size: 13px; } .preset-list small, .agent-list small { margin-top: 5px; color: var(--muted); font-size: 11px; line-height: 1.5; }
.agent-list > div { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.agent-list i { width: 48px; height: 28px; flex: 0 0 48px; padding: 4px 5px; display: flex; justify-content: flex-end; border-radius: 999px; background: var(--primary); }
.agent-list b { width: 20px; height: 20px; border-radius: 50%; background: #fff; }
@media (max-width: 1280px) { .workbench-grid { grid-template-columns: 1fr; } }
@media (max-width: 760px) { .workbench-intro { flex-direction: column; } .api-state { width: 100%; } .configuration-grid { grid-template-columns: 1fr; } }
</style>
