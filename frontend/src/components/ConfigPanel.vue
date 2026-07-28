<template>
  <section class="connection-panel surface-card" aria-labelledby="connection-title">
    <header class="panel-head">
      <div>
        <p class="overline">Bring your own key</p>
        <h2 id="connection-title">连接你的模型</h2>
      </div>
      <span class="protocol-badge">{{ activeProvider.protocol === 'anthropic' ? 'Anthropic Messages' : 'OpenAI-compatible' }}</span>
    </header>

    <div class="provider-strip" role="radiogroup" aria-label="API 供应商">
      <button
        v-for="provider in providers"
        :key="provider.id"
        type="button"
        class="provider-option"
        :class="{ active: modelValue.provider === provider.id }"
        :aria-checked="modelValue.provider === provider.id"
        role="radio"
        @click="selectProvider(provider)"
      >
        <span>{{ provider.name }}</span>
        <small>{{ provider.id === 'minimax' ? '原项目默认' : provider.protocol }}</small>
      </button>
    </div>

    <div class="config-grid">
      <label class="field key-field">
        <span>API Key</span>
        <div class="secret-input">
          <input
            :type="showKey ? 'text' : 'password'"
            :value="modelValue.apiKey"
            :placeholder="activeProvider.key_hint"
            autocomplete="off"
            spellcheck="false"
            @input="updateField('apiKey', $event.target.value)"
          />
          <button type="button" @click="showKey = !showKey">{{ showKey ? '隐藏' : '显示' }}</button>
        </div>
      </label>

      <label class="field">
        <span>模型名</span>
        <input
          type="text"
          :value="modelValue.model"
          :placeholder="activeProvider.default_model"
          autocomplete="off"
          spellcheck="false"
          @input="updateField('model', $event.target.value)"
        />
      </label>

      <label class="field">
        <span>评审预设</span>
        <select :value="modelValue.preset" @change="updateField('preset', $event.target.value)">
          <option value="normal">常规项目</option>
          <option value="p0_critical">P0 紧急项目</option>
          <option value="innovation">创新探索项目</option>
        </select>
      </label>

      <div class="connection-test">
        <span class="test-status" :class="testState">{{ testMessage }}</span>
        <button type="button" class="test-button" :disabled="!canTest || testState === 'testing'" @click="testConnection">
          {{ testState === 'testing' ? '验证中…' : '测试连接' }}
        </button>
      </div>
    </div>

    <p class="trust-note">
      <span aria-hidden="true">↳</span>
      Key 会以明文写入当前浏览器的 localStorage，评审时经 Vercel 函数转发给所选模型。请勿在公共或共享设备上保存；评审会并行请求 6 个维度，请关注模型费用。
    </p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { PROVIDER_FALLBACKS, validateProvider } from '../lib/reviewApi.js'

const props = defineProps({
  modelValue: { type: Object, required: true },
  providers: { type: Array, default: () => PROVIDER_FALLBACKS },
})

const emit = defineEmits(['update:modelValue'])
const showKey = ref(false)
const testState = ref('idle')
const testMessage = ref('尚未验证')

const activeProvider = computed(() => (
  props.providers.find((provider) => provider.id === props.modelValue.provider) || props.providers[0] || PROVIDER_FALLBACKS[0]
))
const canTest = computed(() => Boolean(props.modelValue.apiKey?.trim() && props.modelValue.model?.trim()))

function updateField(field, value) {
  testState.value = 'idle'
  testMessage.value = '配置已修改，尚未验证'
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

function selectProvider(provider) {
  emit('update:modelValue', { ...props.modelValue, provider: provider.id, model: provider.default_model })
  testState.value = 'idle'
  testMessage.value = '供应商已切换，尚未验证'
}

async function testConnection() {
  if (!canTest.value) return
  testState.value = 'testing'
  testMessage.value = '正在发送最小验证请求'
  try {
    const result = await validateProvider({
      provider: props.modelValue.provider,
      apiKey: props.modelValue.apiKey,
      model: props.modelValue.model,
    })
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
.provider-strip { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); border-bottom: 1px solid var(--line); }
.provider-option { min-width: 0; padding: 15px 12px; display: grid; gap: 4px; border: 0; border-right: 1px solid var(--line); background: var(--soft); color: var(--ink); text-align: left; cursor: pointer; }
.provider-option:last-child { border-right: 0; }
.provider-option:hover { background: #fff7e9; }
.provider-option.active { background: var(--primary); color: #fff; }
.provider-option span { overflow: hidden; font-weight: 800; text-overflow: ellipsis; white-space: nowrap; }
.provider-option small { opacity: .7; font-size: 10px; }
.config-grid { padding: 24px 26px; display: grid; grid-template-columns: minmax(250px, 1.35fr) minmax(190px, .9fr) minmax(170px, .65fr) auto; align-items: end; gap: 16px; }
.field { min-width: 0; display: grid; gap: 8px; color: var(--muted); font-size: 12px; font-weight: 700; }
.field input, .field select { width: 100%; box-sizing: border-box; min-height: 44px; padding: 0 13px; border: 1px solid var(--line); border-radius: 13px; background: #fff; color: var(--ink); font: 13px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; }
.field input:focus, .field select:focus { border-color: var(--primary); outline: 3px solid rgb(239 108 0 / 14%); }
.secret-input { display: flex; }
.secret-input input { border-radius: 13px 0 0 13px; }
.secret-input button { padding: 0 14px; border: 1px solid var(--line); border-left: 0; border-radius: 0 13px 13px 0; background: var(--soft); color: var(--primary); cursor: pointer; font-weight: 700; }
.connection-test { display: grid; gap: 8px; }
.test-status { max-width: 160px; overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.test-status.success { color: var(--success); }
.test-status.error { color: var(--danger); }
.test-button { min-height: 44px; padding: 0 18px; border: 0; border-radius: 999px; background: var(--primary); color: #fff; cursor: pointer; font-weight: 800; white-space: nowrap; }
.test-button:disabled { cursor: not-allowed; opacity: .45; }
.trust-note { margin: 0; padding: 16px 26px; display: flex; gap: 9px; border-top: 1px solid var(--line); background: #fff8ed; color: var(--muted); font-size: 12px; line-height: 1.7; }
.trust-note span { color: var(--primary); }
@media (max-width: 1060px) { .provider-strip { grid-template-columns: repeat(3, 1fr); } .provider-option { border-bottom: 1px solid var(--line); } .config-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 650px) { .provider-strip, .config-grid { grid-template-columns: 1fr; } .provider-option { border-right: 0; } .panel-head { align-items: flex-start; flex-direction: column; } }
</style>
