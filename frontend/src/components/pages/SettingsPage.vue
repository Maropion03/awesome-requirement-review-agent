<template>
  <main class="page-shell settings-page">
    <PageHeader
      title="API 设置"
      description="选择接口格式并保存 Base URL 与凭据。配置只保存在当前浏览器，Vercel 后端保持无状态。"
      :can-view-report="canViewReport"
      :can-open-assistant="canOpenAssistant"
      @navigate="$emit('navigate', $event)"
    />

    <section class="settings-intro surface-card">
      <div class="intro-icon">⌁</div>
      <div>
        <p class="overline">Bring your own key</p>
        <h1>连接你的模型</h1>
        <p>支持 OpenAI Chat Completions、OpenAI Responses 和 Anthropic Messages 三种接口格式。</p>
      </div>
      <span class="saved-state" :class="{ ready: Boolean(apiConfig.apiKey) }">{{ apiConfig.apiKey ? '已持久化' : '等待配置' }}</span>
    </section>

    <ConfigPanel :model-value="apiConfig" :formats="formats" @update:model-value="$emit('update:api-config', $event)" />

    <footer class="settings-footer surface-card">
      <div>
        <strong>本地持久化说明</strong>
        <p>Base URL 与 API Key 会写入此浏览器的 localStorage，不会进入仓库、Vercel 环境变量、数据库或服务端日志。</p>
      </div>
      <button class="clear-button" type="button" @click="$emit('clear-api-config')">清除本地配置</button>
      <button class="pill-button primary" type="button" :disabled="!apiConfig.baseUrl || !apiConfig.apiKey || !apiConfig.model" @click="$emit('navigate', 'workbench')">保存并返回工作台</button>
    </footer>
  </main>
</template>

<script setup>
import ConfigPanel from '../ConfigPanel.vue'
import PageHeader from '../layout/PageHeader.vue'

defineProps({
  apiConfig: { type: Object, required: true },
  formats: { type: Array, default: () => [] },
  canViewReport: Boolean,
  canOpenAssistant: Boolean,
})

defineEmits(['navigate', 'update:api-config', 'clear-api-config'])
</script>

<style scoped>
.settings-page { color: var(--ink); }
.settings-intro { margin-bottom: 24px; padding: 26px; display: grid; grid-template-columns: auto minmax(0,1fr) auto; align-items: center; gap: 20px; }
.intro-icon { width: 62px; height: 62px; display: grid; place-items: center; border-radius: 20px; background: var(--soft); color: var(--primary); font-size: 30px; }
h1 { margin: 8px 0 0; font-size: 25px; }
.settings-intro p:last-child, .settings-footer p { margin: 8px 0 0; color: var(--muted); font-size: 13px; line-height: 1.7; }
.saved-state { padding: 8px 12px; border-radius: 999px; background: var(--soft); color: var(--muted); font-size: 12px; font-weight: 700; }
.saved-state.ready { background: #e8f5ec; color: var(--success); }
.settings-footer { margin-top: 24px; padding: 22px 24px; display: flex; align-items: center; gap: 14px; }
.settings-footer > div { flex: 1; }
.clear-button { min-height: 38px; padding: 0 15px; border: 0; background: transparent; color: var(--danger); cursor: pointer; font-weight: 700; }
@media (max-width: 760px) { .settings-intro { grid-template-columns: auto 1fr; } .saved-state { grid-column: 1/-1; width: fit-content; } .settings-footer { align-items: stretch; flex-direction: column; } }
</style>
