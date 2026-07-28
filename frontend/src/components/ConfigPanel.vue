<template>
  <section class="connection-panel" aria-labelledby="connection-title">
    <header class="panel-head">
      <div class="step-mark">02</div>
      <div>
        <p class="eyebrow">Bring your own key</p>
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
        <button
          type="button"
          class="test-button"
          :disabled="!canTest || testState === 'testing'"
          @click="testConnection"
        >
          {{ testState === 'testing' ? '验证中…' : '测试连接' }}
        </button>
      </div>
    </div>

    <p class="trust-note">
      <span aria-hidden="true">↳</span>
      Key 仅随本次请求发送到 Vercel 函数和所选模型服务，不写入 localStorage、数据库或日志。评审会把文档并行发送 6 次，请关注模型费用。
    </p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { PROVIDER_FALLBACKS, validateProvider } from '../lib/reviewApi.js'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  providers: {
    type: Array,
    default: () => PROVIDER_FALLBACKS,
  },
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
  emit('update:modelValue', {
    ...props.modelValue,
    provider: provider.id,
    model: provider.default_model,
  })
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
.connection-panel {
  border: 1px solid #1f1d19;
  border-radius: 18px;
  background: #fffdf8;
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border-bottom: 1px solid #ded8cc;
}

.step-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  background: #ff5a1f;
  color: #fff;
  border-radius: 50%;
  font: 700 13px/1 ui-monospace, SFMono-Regular, Menlo, monospace;
}

.eyebrow,
h2 {
  margin: 0;
}

.eyebrow {
  color: #716b60;
  text-transform: uppercase;
  letter-spacing: .12em;
  font-size: 10px;
  font-weight: 700;
}

h2 {
  font: 650 19px/1.2 'Avenir Next', 'PingFang SC', sans-serif;
}

.protocol-badge {
  margin-left: auto;
  border: 1px solid #1f1d19;
  border-radius: 999px;
  padding: 7px 10px;
  font: 600 11px/1 ui-monospace, SFMono-Regular, Menlo, monospace;
}

.provider-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  border-bottom: 1px solid #ded8cc;
}

.provider-option {
  min-width: 0;
  border: 0;
  border-right: 1px solid #ded8cc;
  background: #f7f2e8;
  padding: 13px 10px;
  display: grid;
  gap: 3px;
  text-align: left;
  cursor: pointer;
  color: #211f1a;
}

.provider-option:last-child { border-right: 0; }
.provider-option:hover { background: #fff7e9; }
.provider-option.active { background: #1f1d19; color: #fff; }
.provider-option span { font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.provider-option small { opacity: .62; font: 10px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; }

.config-grid {
  display: grid;
  grid-template-columns: minmax(240px, 1.35fr) minmax(190px, .9fr) minmax(170px, .65fr) auto;
  align-items: end;
  gap: 14px;
  padding: 20px;
}

.field {
  min-width: 0;
  display: grid;
  gap: 7px;
  color: #514b42;
  font-size: 12px;
  font-weight: 700;
}

.field input,
.field select {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #bcb4a7;
  border-radius: 10px;
  background: #fff;
  color: #1f1d19;
  padding: 11px 12px;
  font: 13px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
}

.field input:focus,
.field select:focus { border-color: #ff5a1f; outline: 3px solid rgba(255, 90, 31, .16); }

.secret-input { display: flex; }
.secret-input input { border-radius: 10px 0 0 10px; }
.secret-input button {
  border: 1px solid #bcb4a7;
  border-left: 0;
  border-radius: 0 10px 10px 0;
  background: #f0ebe1;
  padding: 0 12px;
  cursor: pointer;
  font-weight: 700;
}

.connection-test { display: grid; gap: 7px; justify-items: end; }
.test-status { max-width: 190px; color: #716b60; font-size: 11px; text-align: right; line-height: 1.25; }
.test-status.success { color: #137044; }
.test-status.error { color: #b42318; }
.test-button {
  border: 1px solid #1f1d19;
  border-radius: 10px;
  background: #fff;
  color: #1f1d19;
  padding: 11px 15px;
  font-weight: 750;
  cursor: pointer;
  white-space: nowrap;
}
.test-button:disabled { opacity: .45; cursor: not-allowed; }

.trust-note {
  margin: 0;
  padding: 12px 20px;
  border-top: 1px solid #ded8cc;
  background: #fff6d9;
  color: #5e5132;
  font-size: 12px;
  line-height: 1.5;
}
.trust-note span { color: #ff5a1f; font-weight: 900; margin-right: 7px; }

@media (max-width: 1050px) {
  .provider-strip { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .config-grid { grid-template-columns: 1fr 1fr; }
  .connection-test { justify-items: start; }
  .test-status { text-align: left; }
}

@media (max-width: 640px) {
  .panel-head { align-items: flex-start; }
  .protocol-badge { display: none; }
  .provider-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .config-grid { grid-template-columns: 1fr; }
}
</style>
