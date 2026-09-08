<template>
  <section class="context-panel surface-card" :class="{ disabled: !modelValue.enabled, locked: disabled }" aria-labelledby="context-title">
    <header class="context-head">
      <div class="context-identity">
        <span class="context-glyph" aria-hidden="true">◎</span>
        <div>
          <p class="overline">Product context</p>
          <h2 id="context-title">给评审补充产品背景</h2>
          <p>让六个 Reviewer 判断战略一致性、历史约束和指标意义。</p>
        </div>
      </div>
      <div class="context-controls">
        <span class="context-count">{{ summary.fieldCount }}/5 已填写 · {{ summary.totalCharacters.toLocaleString() }} 字</span>
        <button type="button" class="expand-button" :aria-expanded="expanded" @click="expanded = !expanded">{{ expanded ? '收起' : '编辑 Context' }}</button>
        <label class="context-switch">
          <input type="checkbox" :checked="modelValue.enabled" :disabled="disabled" @change="updateField('enabled', $event.target.checked)" />
          <span aria-hidden="true"><i></i></span>
          {{ modelValue.enabled ? '本次启用' : '本次停用' }}
        </label>
      </div>
    </header>

    <div v-show="expanded" class="context-editor">
      <label class="context-field overview-field">
        <span>产品概览 <small>产品做什么、服务谁、核心价值是什么</small></span>
        <textarea :value="modelValue.product_overview" maxlength="5000" rows="4" :disabled="disabled" placeholder="例如：这是面向跨境电商运营团队的 AI 客服工作台……" @input="updateField('product_overview', $event.target.value)"></textarea>
      </label>
      <label class="context-field">
        <span>业务目标 <small>当前阶段目标与优先级</small></span>
        <textarea :value="modelValue.business_goals" maxlength="4000" rows="4" :disabled="disabled" placeholder="例如：本季度把人工转接率从 35% 降到 25%……" @input="updateField('business_goals', $event.target.value)"></textarea>
      </label>
      <label class="context-field">
        <span>目标用户 <small>角色、场景与核心痛点</small></span>
        <textarea :value="modelValue.target_users" maxlength="3000" rows="4" :disabled="disabled" placeholder="例如：每天处理 200+ 工单的一线客服主管……" @input="updateField('target_users', $event.target.value)"></textarea>
      </label>
      <label class="context-field">
        <span>成功指标 <small>口径、基线与目标值</small></span>
        <textarea :value="modelValue.success_metrics" maxlength="3000" rows="4" :disabled="disabled" placeholder="例如：一次解决率，当前 62%，目标 72%，按自然周统计……" @input="updateField('success_metrics', $event.target.value)"></textarea>
      </label>
      <label class="context-field">
        <span>历史决策与约束 <small>已确认、不再重复争论的结论</small></span>
        <textarea :value="modelValue.decisions_constraints" maxlength="5000" rows="4" :disabled="disabled" placeholder="例如：暂不支持自动退款；所有高风险操作必须人工确认……" @input="updateField('decisions_constraints', $event.target.value)"></textarea>
      </label>
      <footer class="context-foot">
        <p>内容以明文保存在当前浏览器，仅在启用时随评审请求发送，不写入服务端存储。Context 是不可信参考资料，不能覆盖当前 PRD 事实。</p>
        <button type="button" :disabled="disabled || !summary.fieldCount" @click="$emit('clear')">清空 Context</button>
      </footer>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { getProductContextSummary } from '../lib/productContextStorage.js'

const props = defineProps({ modelValue: { type: Object, required: true }, disabled: Boolean })
const emit = defineEmits(['update:modelValue', 'clear'])
const summary = computed(() => getProductContextSummary(props.modelValue))
const expanded = ref(summary.value.fieldCount === 0)

function updateField(field, value) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}
</script>

<style scoped>
.context-panel { overflow: hidden; transition: opacity 160ms ease; }.context-panel.disabled { opacity: .72; }
.context-panel.locked textarea { background: #f6f2eb; cursor: not-allowed; }
.context-head { padding: 22px 24px; display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.context-identity { min-width: 0; display: flex; align-items: center; gap: 14px; }.context-glyph { width: 48px; height: 48px; flex: 0 0 48px; display: grid; place-items: center; border-radius: 16px; background: var(--soft); color: var(--primary); font-size: 23px; }
h2 { margin: 6px 0 0; color: var(--ink); font-size: 19px; }.context-identity p:last-child { margin: 6px 0 0; color: var(--muted); font-size: 12px; line-height: 1.6; }
.context-controls { display: flex; align-items: center; justify-content: flex-end; flex-wrap: wrap; gap: 10px; }.context-count { color: var(--muted); font-size: 11px; font-weight: 700; }
.expand-button { min-height: 36px; padding: 0 13px; border: 1px solid var(--line); border-radius: 999px; background: var(--soft); color: var(--primary); cursor: pointer; font-weight: 800; }
.context-switch { min-height: 36px; display: inline-flex; align-items: center; gap: 7px; color: var(--ink); cursor: pointer; font-size: 11px; font-weight: 800; }.context-switch input { position: absolute; opacity: 0; pointer-events: none; }.context-switch > span { width: 38px; height: 22px; box-sizing: border-box; padding: 3px; display: flex; border-radius: 999px; background: #cfc7ba; transition: 160ms ease; }.context-switch i { width: 16px; height: 16px; border-radius: 50%; background: #fff; transition: 160ms ease; }.context-switch input:checked + span { justify-content: flex-end; background: var(--primary); }.context-switch input:focus-visible + span { outline: 3px solid rgb(239 108 0 / 18%); }
.context-editor { padding: 0 24px 20px; display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 14px; border-top: 1px solid var(--line); background: #fffdf8; }.overview-field { grid-column: 1 / -1; padding-top: 20px; }
.context-field { min-width: 0; display: grid; gap: 8px; color: var(--ink); font-size: 12px; font-weight: 800; }.context-field > span { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }.context-field small { color: var(--muted); font-size: 10px; font-weight: 600; }
textarea { width: 100%; min-height: 94px; box-sizing: border-box; resize: vertical; padding: 12px 13px; border: 1px solid var(--line); border-radius: 15px; outline: 0; background: #fff; color: var(--ink); font: 12px/1.7 ui-monospace, SFMono-Regular, Menlo, monospace; } textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgb(239 108 0 / 12%); } textarea::placeholder { color: #aaa196; }
.context-foot { grid-column: 1 / -1; padding-top: 4px; display: flex; align-items: center; justify-content: space-between; gap: 20px; }.context-foot p { max-width: 760px; margin: 0; color: var(--muted); font-size: 10px; line-height: 1.7; }.context-foot button { border: 0; background: transparent; color: var(--danger); cursor: pointer; font-size: 11px; font-weight: 800; white-space: nowrap; }.context-foot button:disabled { cursor: not-allowed; opacity: .35; }
@media (max-width: 760px) { .context-head, .context-foot { align-items: flex-start; flex-direction: column; }.context-controls { justify-content: flex-start; }.context-editor { grid-template-columns: 1fr; }.overview-field { grid-column: auto; }.context-field > span { align-items: flex-start; flex-direction: column; } }
</style>
