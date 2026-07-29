<template>
  <aside class="sidebar">
    <header class="brand-block">
      <h1>PRD 评审工作台</h1>
      <span class="global-status"><i :class="runStatus"></i>{{ statusLabel }}</span>
    </header>

    <nav class="nav-list" aria-label="主导航">
      <button v-for="item in navItems" :key="item.id" type="button" :class="{ active: activePage === item.id }" @click="$emit('navigate', item.id)">
        <span class="nav-icon" aria-hidden="true">{{ item.icon }}</span>{{ item.label }}
      </button>
    </nav>

    <section class="run-card">
      <p>Current Run</p>
      <dl>
        <div><dt>Provider</dt><dd>{{ providerName || '未配置' }}</dd></div>
        <div><dt>Preset</dt><dd>{{ preset }}</dd></div>
        <div><dt>Progress</dt><dd>{{ progress }}%</dd></div>
      </dl>
    </section>

    <button class="new-project" type="button" @click="$emit('new-project')">＋ 新项目</button>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  activePage: { type: String, default: 'workbench' },
  runStatus: { type: String, default: 'idle' },
  preset: { type: String, default: 'normal' },
  progress: { type: Number, default: 0 },
  providerName: { type: String, default: '' },
})

defineEmits(['navigate', 'new-project'])

const navItems = [
  { id: 'workbench', label: '工作台', icon: '▦' },
  { id: 'report', label: '评审报告', icon: '▤' },
  { id: 'assistant', label: '评审助手', icon: '✦' },
  { id: 'settings', label: 'API 设置', icon: '⚙' },
]

const statusLabel = computed(() => ({
  idle: '就绪', reviewing: '评审中', completed: '已完成', error: '异常',
}[props.runStatus] || '就绪'))
</script>

<style scoped>
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 100;
  width: 288px;
  padding: 28px 20px 24px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(221, 212, 198, 0.8);
  background: rgba(239, 231, 219, 0.88);
  backdrop-filter: blur(18px);
}
.brand-block { margin-bottom: 28px; display: block; }
h1 { margin: 0; color: var(--ink); font: italic 600 29px/1.1 var(--font-display); white-space: nowrap; }
.global-status { padding: 6px 9px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 999px; background: var(--panel); color: var(--muted); font-size: 10px; font-weight: 700; white-space: nowrap; }
.brand-block .global-status { margin-top: 14px; }
.global-status i { width: 7px; height: 7px; border-radius: 50%; background: #38a169; }
.global-status i.reviewing { background: var(--primary); animation: pulse 1.1s infinite; }
.global-status i.error { background: var(--danger); }
.nav-list { display: grid; gap: 8px; }
.nav-list button { width: 100%; min-height: 46px; padding: 0 16px; display: flex; align-items: center; gap: 12px; border: 0; border-radius: 16px; background: transparent; color: var(--muted); cursor: pointer; text-align: left; font-size: 14px; font-weight: 700; transition: 160ms ease; }
.nav-list button:hover { background: rgba(255,253,248,.58); color: var(--ink); }
.nav-list button.active { background: var(--panel); color: var(--primary); box-shadow: 0 10px 24px rgba(31,29,25,.08); }
.nav-icon { width: 20px; display: inline-grid; place-items: center; font-size: 17px; }
.run-card { margin-top: 30px; padding: 20px; border: 1px solid rgba(221,212,198,.8); border-radius: 24px; background: var(--panel); box-shadow: var(--shadow-card); }
.run-card > p { margin: 0; color: var(--muted); font-size: 10px; font-weight: 700; letter-spacing: .32em; text-transform: uppercase; }
dl { margin: 17px 0 0; display: grid; gap: 13px; }
dl div { display: flex; justify-content: space-between; gap: 12px; font-size: 12px; }
dt { color: var(--muted); } dd { max-width: 122px; margin: 0; overflow: hidden; color: var(--ink); font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.new-project { margin-top: auto; min-height: 42px; border: 0; border-radius: 14px; background: transparent; color: var(--muted); cursor: pointer; text-align: left; font-weight: 700; }
.new-project:hover { color: var(--primary); }
@keyframes pulse { 50% { opacity: .35; } }
@media (max-width: 1020px) {
  .sidebar { inset: 0 0 auto; width: auto; height: auto; padding: 16px 20px; border-right: 0; border-bottom: 1px solid var(--line); }
  .brand-block { margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .brand-block .global-status { margin-top: 0; }
  .nav-list { grid-template-columns: repeat(4, minmax(0,1fr)); }
  .nav-list button { justify-content: center; padding: 0 10px; }
  .run-card, .new-project { display: none; }
}
@media (max-width: 640px) { .nav-list { grid-template-columns: repeat(2,minmax(0,1fr)); } h1 { font-size: 24px; } }
</style>
