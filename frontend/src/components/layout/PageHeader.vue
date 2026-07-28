<template>
  <header class="page-header surface-card">
    <div>
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
    </div>
    <nav aria-label="页面快捷导航">
      <button type="button" @click="$emit('navigate', 'workbench')">工作台</button>
      <button type="button" :disabled="!canViewReport" @click="$emit('navigate', 'report')">报告</button>
      <button type="button" :disabled="!canOpenAssistant" @click="$emit('navigate', 'assistant')">助手</button>
      <button type="button" @click="$emit('navigate', 'settings')">API 设置</button>
    </nav>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  canViewReport: Boolean,
  canOpenAssistant: Boolean,
})

defineEmits(['navigate'])
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
  padding: 20px 24px;
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
  background: rgba(255, 253, 248, 0.86);
  backdrop-filter: blur(18px);
}
h2 { margin: 0; color: var(--ink); font: 400 clamp(30px, 3.2vw, 42px)/1 var(--font-display); }
p { max-width: 760px; margin: 9px 0 0; color: var(--muted); font-size: 13px; line-height: 1.8; }
nav { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 10px; }
button { min-height: 36px; padding: 0 15px; border: 1px solid var(--line); border-radius: 999px; background: var(--soft); color: var(--primary); cursor: pointer; font-size: 13px; font-weight: 700; }
button:hover:not(:disabled) { background: var(--panel); }
button:disabled { cursor: not-allowed; opacity: 0.38; }
@media (max-width: 760px) { .page-header { align-items: start; flex-direction: column; } nav { justify-content: flex-start; } }
</style>
