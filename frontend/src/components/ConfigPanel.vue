<template>
  <section class="connection-panel surface-card" aria-labelledby="connection-title">
    <header class="panel-head">
      <div><p class="overline">Bring your own endpoint</p><h2 id="connection-title">连接你的模型接口</h2></div>
      <span class="protocol-badge">{{ activeFormat.endpoint_hint }}</span>
    </header>

    <div class="format-strip" role="radiogroup" aria-label="API 接口格式">
      <button
        v-for="format in formats"
        :key="format.id"
        type="button"
        class="format-option"
        :class="{ active: modelValue.apiFormat === format.id }"
        :aria-checked="modelValue.apiFormat === format.id"
        role="radio"
        @click="selectFormat(format)"
      >
        <span>{{ format.name }}</span><small>{{ format.endpoint_hint }}</small>
      </button>
    </div>

    <div class="config-grid">
      <label class="field base-url-field">
        <span>Base URL</span>
        <input type="url" :value="modelValue.baseUrl" :placeholder="activeFormat.default_base_url" autocomplete="off" spellcheck="false" @input="updateField('baseUrl', $event.target.value)" />
      </label>
      <label class="field key-field">
        <span>API Key</span>
        <div class="secret-input">
          <input :type="showKey ? 'text' : 'password'" :value="modelValue.apiKey" :placeholder="activeFormat.key_hint" autocomplete="off" spellcheck="false" @input="updateField('apiKey', $event.target.value)" />
          <button type="button" @click="showKey = !showKey">{{ showKey ? '隐藏' : '显示' }}</button>
        </div>
      </label>
      <label class="field review-model-field">
        <span>正文评审模型</span>
        <input type="text" :value="modelValue.model" :placeholder="activeFormat.default_model" autocomplete="off" spellcheck="false" @input="updateField('model', $event.target.value)" />
      </label>
      <label class="field vision-model-field">
        <span>视觉模型（PDF 流程图）</span>
        <input type="text" :value="modelValue.visionModel" placeholder="留空则使用正文模型" autocomplete="off" spellcheck="false" @input="updateField('visionModel', $event.target.value)" />
      </label>
      <label class="field preset-field">
        <span>评审预设</span>
        <select :value="modelValue.preset" @change="updateField('preset', $event.target.value)">
          <option value="normal">常规项目</option><option value="p0_critical">P0 紧急项目</option><option value="innovation">创新探索项目</option>
        </select>
      </label>
      <div class="connection-test">
        <span class="test-status" :class="testState">{{ testMessage }}</span>
        <button type="button" class="test-button" :disabled="!canTest || testState === 'testing'" @click="testConnection">{{ testState === 'testing' ? '验证中…' : '测试连接' }}</button>
      </div>
    </div>

    <p v-if="textOnlyModel" class="model-warning" role="status">
      <strong>{{ modelCapability.family }} 仅支持文本输入。</strong>
      它可以继续负责正文评审；PDF 流程图会使用 {{ effectiveVisionModel }}。若两者相同，请填写一个支持图片的视觉模型。
    </p>

    <p class="trust-note"><span aria-hidden="true">↳</span>Key 与 Base URL 会以明文写入当前浏览器的 localStorage。视觉模型留空时复用正文模型；智谱官方地址的 GLM-5.3 旧配置会自动使用 glm-4.6v-flash 识别流程图。服务端仅访问公网 HTTPS 443 端点且不跟随重定向。</p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { resolveVisionModel } from '../lib/apiConfigStorage.js'
import { detectModelCapability } from '../lib/modelCapabilities.js'
import { API_FORMAT_FALLBACKS, validateFormat } from '../lib/reviewApi.js'

const props = defineProps({
  modelValue: { type: Object, required: true },
  formats: { type: Array, default: () => API_FORMAT_FALLBACKS },
})
const emit = defineEmits(['update:modelValue'])
const showKey = ref(false)
const testState = ref('idle')
const testMessage = ref('尚未验证')
const activeFormat = computed(() => props.formats.find((format) => format.id === props.modelValue.apiFormat) || props.formats[0] || API_FORMAT_FALLBACKS[0])
const canTest = computed(() => Boolean(props.modelValue.baseUrl?.trim() && props.modelValue.apiKey?.trim() && props.modelValue.model?.trim()))
const modelCapability = computed(() => detectModelCapability(props.modelValue.model))
const textOnlyModel = computed(() => modelCapability.value.capability === 'text_only')
const effectiveVisionModel = computed(() => resolveVisionModel(props.modelValue))

function updateField(field, value) {
  testState.value = 'idle'
  testMessage.value = '配置已修改，尚未验证'
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

function selectFormat(format) {
  emit('update:modelValue', {
    ...props.modelValue,
    apiFormat: format.id,
    baseUrl: format.default_base_url,
    model: format.default_model,
    visionModel: '',
  })
  testState.value = 'idle'
  testMessage.value = '接口格式已切换，尚未验证'
}

async function testConnection() {
  if (!canTest.value) return
  testState.value = 'testing'
  testMessage.value = '正在发送最小验证请求'
  try {
    const result = await validateFormat({ apiFormat: props.modelValue.apiFormat, endpointBaseUrl: props.modelValue.baseUrl, apiKey: props.modelValue.apiKey, model: props.modelValue.model })
    testState.value = 'success'
    testMessage.value = result.message || '连接成功'
  } catch (error) {
    testState.value = 'error'
    testMessage.value = error instanceof Error ? error.message : '连接失败'
  }
}
</script>

<style scoped>
.connection-panel { overflow: hidden; }
.panel-head { padding: 24px 26px; display: flex; align-items: center; justify-content: space-between; gap: 18px; border-bottom: 1px solid var(--line); }
h2 { margin: 7px 0 0; font-size: 24px; }
.protocol-badge { padding: 8px 12px; border-radius: 999px; background: var(--soft); color: var(--primary); font: 700 11px/1 ui-monospace, SFMono-Regular, Menlo, monospace; }
.format-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-bottom: 1px solid var(--line); }
.format-option { min-width: 0; padding: 17px 16px; display: grid; gap: 5px; border: 0; border-right: 1px solid var(--line); background: var(--soft); color: var(--ink); text-align: left; cursor: pointer; }
.format-option:last-child { border-right: 0; }.format-option:hover { background: #fff7e9; }.format-option.active { background: var(--primary); color: #fff; }
.format-option span { overflow: hidden; font-weight: 800; text-overflow: ellipsis; white-space: nowrap; }.format-option small { opacity: .72; font: 10px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; }
.config-grid { padding: 24px 26px; display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); align-items: end; gap: 14px; }
.base-url-field { grid-column: span 5; }.key-field { grid-column: span 4; }.review-model-field { grid-column: span 3; }
.vision-model-field { grid-column: span 5; }.preset-field { grid-column: span 3; }.connection-test { grid-column: span 4; }
.field { min-width: 0; display: grid; gap: 8px; color: var(--muted); font-size: 12px; font-weight: 700; }
.field input, .field select { width: 100%; box-sizing: border-box; min-height: 44px; padding: 0 13px; border: 1px solid var(--line); border-radius: 13px; background: #fff; color: var(--ink); font: 13px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; }
.field input:focus, .field select:focus { border-color: var(--primary); outline: 3px solid rgb(239 108 0 / 14%); }
.secret-input { display: flex; }.secret-input input { border-radius: 13px 0 0 13px; }.secret-input button { padding: 0 14px; border: 1px solid var(--line); border-left: 0; border-radius: 0 13px 13px 0; background: var(--soft); color: var(--primary); cursor: pointer; font-weight: 700; }
.connection-test { display: grid; gap: 8px; }.test-status { max-width: 150px; overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }.test-status.success { color: var(--success); }.test-status.error { color: var(--danger); }
.test-button { min-height: 44px; padding: 0 17px; border: 0; border-radius: 999px; background: var(--primary); color: #fff; cursor: pointer; font-weight: 800; white-space: nowrap; }.test-button:disabled { cursor: not-allowed; opacity: .45; }
.model-warning { margin: 0; padding: 14px 26px; border-top: 1px solid #edc8bd; background: #fff1ed; color: #854138; font-size: 12px; line-height: 1.7; }.model-warning strong { margin-right: 4px; color: #a33428; }
.trust-note { margin: 0; padding: 16px 26px; display: flex; gap: 9px; border-top: 1px solid var(--line); background: #fff8ed; color: var(--muted); font-size: 12px; line-height: 1.7; }.trust-note span { color: var(--primary); }
@media (max-width: 1180px) { .config-grid { grid-template-columns: 1fr 1fr; } .base-url-field, .key-field, .review-model-field, .vision-model-field, .preset-field, .connection-test { grid-column: auto; } }
@media (max-width: 650px) { .format-strip, .config-grid { grid-template-columns: 1fr; } .format-option { border-right: 0; border-bottom: 1px solid var(--line); } .panel-head { align-items: flex-start; flex-direction: column; } }
</style>
