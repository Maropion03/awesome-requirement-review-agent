<template>
  <aside class="progress-panel surface-card">
    <header><div><p class="overline">Review Stream</p><h2>实时进度</h2></div><span>{{ statusLabel }}</span></header>

    <section class="terminal">
      <div class="terminal-title"><i></i><i></i><i></i><span>agent_terminal.sh</span></div>
      <div class="terminal-log">
        <p class="success">[SYSTEM] Vercel stateless runtime ready.</p>
        <p class="info">[API] BYOK provider request configured.</p>
        <p v-for="(line, index) in outputLines" :key="`${line}-${index}`" :class="lineTone(line)">{{ line }}</p>
        <p v-if="!streamText" class="muted">[WAITING] Waiting for document upload...</p>
      </div>
      <footer><div><span>总体进度</span><b>{{ progress }}%</b></div><div class="progress-track"><i :style="{ width: `${progress}%` }"></i></div></footer>
    </section>

    <div class="actions">
      <button class="primary" type="button" :disabled="!canStart" @click="$emit('start-review')">{{ isRunning ? '正在执行评审' : '开始执行评审' }}</button>
      <button type="button" :disabled="isRunning" @click="$emit('reset')">重置当前会话</button>
      <button type="button" :disabled="!canViewReport" @click="$emit('navigate', 'report')">切换到报告</button>
      <button type="button" :disabled="!canOpenAssistant" @click="$emit('navigate', 'assistant')">切换到助手</button>
    </div>

    <div class="stage-list">
      <span v-for="stage in agentStages" :key="stage.id" :class="stage.status"><i></i>{{ stage.title }}</span>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ agentStages: { type: Array, default: () => [] }, dimensions: { type: Array, default: () => [] }, streamText: { type: String, default: '' }, isRunning: Boolean, canStart: Boolean, canViewReport: Boolean, canOpenAssistant: Boolean })
defineEmits(['start-review', 'reset', 'navigate'])
const completed = computed(() => props.dimensions.filter((item) => item.status === 'complete').length)
const progress = computed(() => props.dimensions.length ? Math.round((completed.value / props.dimensions.length) * 100) : 0)
const statusLabel = computed(() => props.isRunning ? 'RUNNING' : progress.value === 100 ? 'COMPLETE' : 'WAITING')
const outputLines = computed(() => String(props.streamText || '').split('\n').filter(Boolean).slice(-18))
function lineTone(line) { if (/完成|complete|success/i.test(line)) return 'success'; if (/失败|error|降级/i.test(line)) return 'error'; return 'info' }
</script>

<style scoped>
.progress-panel { position: sticky; top: 28px; padding: 24px; }
header { display: flex; justify-content: space-between; align-items: start; gap: 14px; }
h2 { margin: 8px 0 0; font-size: 18px; }
header > span { padding: 7px 10px; border-radius: 999px; background: var(--soft); color: var(--primary); font-size: 11px; font-weight: 800; }
.terminal { margin-top: 20px; padding: 15px; border-radius: 26px; background: #171a19; color: #e7e5e4; box-shadow: inset 0 2px 12px rgba(0,0,0,.22); }
.terminal-title { padding-bottom: 13px; display: flex; align-items: center; gap: 7px; border-bottom: 1px solid rgba(255,255,255,.1); color: #a8a29e; font: 10px/1 var(--font-mono); letter-spacing: .2em; text-transform: uppercase; }
.terminal-title i { width: 8px; height: 8px; border-radius: 50%; background: #f87171; }.terminal-title i:nth-child(2){background:#fbbf24}.terminal-title i:nth-child(3){background:#34d399}.terminal-title span{margin-left:3px}
.terminal-log { height: 330px; padding: 15px 0; overflow: auto; font: 11px/1.75 var(--font-mono); }
.terminal-log p { margin: 0 0 4px; white-space: pre-wrap; word-break: break-word; }.terminal-log .success{color:#6ee7b7}.terminal-log .info{color:#bae6fd}.terminal-log .error{color:#fca5a5}.terminal-log .muted{color:#a8a29e}
.terminal footer { padding-top: 14px; border-top: 1px solid rgba(255,255,255,.1); }.terminal footer > div:first-child{display:flex;justify-content:space-between;color:#a8a29e;font-size:10px}.progress-track{height:8px;margin-top:9px;overflow:hidden;border-radius:999px;background:rgba(255,255,255,.1)}.progress-track i{display:block;height:100%;border-radius:inherit;background:var(--accent);transition:width .4s ease}
.actions { margin-top: 20px; display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 11px; }.actions button{min-height:44px;padding:8px 12px;border:1px solid var(--line);border-radius:16px;background:var(--soft);color:var(--primary);cursor:pointer;font-size:12px;font-weight:800}.actions button.primary{border-color:var(--primary);background:var(--primary);color:#fff}.actions button:disabled{cursor:not-allowed;opacity:.38}
.stage-list { margin-top: 18px; display: flex; flex-wrap: wrap; gap: 8px; }.stage-list span{padding:6px 9px;display:inline-flex;align-items:center;gap:6px;border-radius:999px;background:var(--soft);color:var(--muted);font-size:10px;font-weight:700}.stage-list i{width:6px;height:6px;border-radius:50%;background:#a8a29e}.stage-list .active i{background:var(--primary)}.stage-list .complete i{background:var(--success)}
@media (max-width:1280px){.progress-panel{position:static}}
</style>
