<template>
  <Teleport to="body">
    <div v-if="open" class="dialog-backdrop" @click.self="$emit('configure')">
      <section ref="dialogElement" class="capability-dialog" role="dialog" aria-modal="true" aria-labelledby="capability-dialog-title" tabindex="-1" @keydown.esc="$emit('configure')">
        <div class="warning-mark" aria-hidden="true">!</div>
        <p class="overline">MODEL CAPABILITY CHECK</p>
        <h2 id="capability-dialog-title">当前正文模型不支持图片</h2>
        <p class="dialog-copy">
          已识别到 <strong>{{ reviewModel }}</strong> 是纯文本模型。正文仍由它评审；PDF 流程图将交给
          <strong>{{ visionModel }}</strong> 识别并转换为 Mermaid。
        </p>
        <p v-if="sameModel" class="risk-copy">当前视觉模型仍与正文模型相同，继续后流程图识别很可能降级。</p>
        <div class="model-route" aria-label="模型分工">
          <span><small>正文评审</small>{{ reviewModel }}</span>
          <i aria-hidden="true">→</i>
          <span><small>流程图识别</small>{{ visionModel }}</span>
        </div>
        <div class="dialog-actions">
          <button type="button" class="secondary-action" @click="$emit('configure')">检查模型设置</button>
          <button type="button" class="primary-action" @click="$emit('continue')">{{ sameModel ? '仍然继续' : '确认并继续' }}</button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  open: Boolean,
  reviewModel: { type: String, default: '' },
  visionModel: { type: String, default: '' },
})
defineEmits(['continue', 'configure'])

const dialogElement = ref(null)
const sameModel = computed(() => props.reviewModel.trim().toLowerCase() === props.visionModel.trim().toLowerCase())

watch(() => props.open, async (isOpen) => {
  if (!isOpen) return
  await nextTick()
  dialogElement.value?.focus()
})
</script>

<style scoped>
.dialog-backdrop { position: fixed; inset: 0; z-index: 1000; display: grid; place-items: center; padding: 24px; background: rgb(30 27 22 / 58%); backdrop-filter: blur(8px); }
.capability-dialog { width: min(520px, 100%); box-sizing: border-box; padding: 30px; border: 1px solid #d9c8ad; border-radius: 28px; outline: 0; background: #fffaf2; box-shadow: 0 30px 90px rgb(48 36 19 / 30%); color: #201d19; animation: dialog-in 180ms ease-out; }
.warning-mark { width: 44px; height: 44px; display: grid; place-items: center; margin-bottom: 20px; border-radius: 50%; background: #ef6c00; color: #fff; font: 900 24px/1 Georgia, serif; }
.overline { margin: 0; color: #a45717; font: 800 10px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: .2em; }
h2 { margin: 9px 0 12px; font: 700 29px/1.2 Georgia, 'Noto Serif SC', serif; }
.dialog-copy, .risk-copy { margin: 0; color: #6d655b; font-size: 14px; line-height: 1.8; }
.dialog-copy strong { color: #24201b; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.risk-copy { margin-top: 12px; padding-left: 12px; border-left: 3px solid #c9473b; color: #a23930; }
.model-route { margin: 22px 0; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 12px; }
.model-route span { min-width: 0; padding: 13px 15px; border: 1px solid #e3d6c4; border-radius: 15px; background: #fff; overflow-wrap: anywhere; font: 700 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; }
.model-route small { display: block; margin-bottom: 5px; color: #8a8176; font: 700 10px/1.2 sans-serif; }
.model-route i { color: #ef6c00; font-style: normal; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; }
.dialog-actions button { min-height: 44px; padding: 0 18px; border-radius: 999px; cursor: pointer; font-weight: 800; }
.secondary-action { border: 1px solid #d9c8ad; background: transparent; color: #5d554b; }
.primary-action { border: 1px solid #ef6c00; background: #ef6c00; color: #fff; }
@keyframes dialog-in { from { opacity: 0; transform: translateY(10px) scale(.98); } }
@media (max-width: 560px) { .capability-dialog { padding: 24px; border-radius: 22px; } h2 { font-size: 24px; } .model-route { grid-template-columns: 1fr; } .model-route i { transform: rotate(90deg); justify-self: center; } .dialog-actions { align-items: stretch; flex-direction: column-reverse; } .dialog-actions button { width: 100%; } }
@media (prefers-reduced-motion: reduce) { .capability-dialog { animation: none; } }
</style>
