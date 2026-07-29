<template>
  <section class="upload-card surface-card" :class="{ dragging: isDragging, error: errorMessage }">
    <label @dragover.prevent="isDragging = true" @dragleave.prevent="isDragging = false" @drop.prevent="handleDrop">
      <input type="file" accept=".md,.docx" :disabled="disabled" @change="handleFileChange" />
      <template v-if="!modelValue">
        <span class="file-icon" aria-hidden="true">▤</span>
        <strong>拖拽 PRD 到这里</strong>
        <p>支持 `.md` 和 `.docx`，大小不超过 3.5MB。上传成功后即可启动无状态评审。</p>
        <span class="choose-button">选择文件</span>
      </template>
      <template v-else>
        <span class="file-icon ready" aria-hidden="true">✓</span>
        <strong>{{ modelValue }}</strong>
        <p>{{ errorMessage || statusDescription }}</p>
        <span class="choose-button secondary">更换文件</span>
      </template>
    </label>
    <button v-if="modelValue" type="button" :disabled="disabled" @click="clearSelection">清除</button>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
const props = defineProps({ modelValue: { type: String, default: '' }, status: { type: String, default: 'idle' }, errorMessage: { type: String, default: '' }, disabled: Boolean })
const emit = defineEmits(['update:modelValue', 'file-selected', 'clear-file'])
const isDragging = ref(false)
const statusDescription = computed(() => ({ ready: '文档已选择，等待开始评审。', uploading: '正在上传并分析文档…', uploaded: '评审已完成，可查看报告。', error: '文档处理失败。' }[props.status] || '等待文档。'))
function emitFile(file) { if (!file || props.disabled) return; emit('update:modelValue', file.name); emit('file-selected', file) }
function handleFileChange(event) { emitFile(event.target.files?.[0]) }
function handleDrop(event) { isDragging.value = false; emitFile(event.dataTransfer?.files?.[0]) }
function clearSelection() { emit('update:modelValue', ''); emit('clear-file') }
</script>

<style scoped>
.upload-card { position: relative; overflow: hidden; border-style: dashed; border-width: 2px; transition: 160ms ease; }
.upload-card.dragging { border-color: var(--primary); background: rgba(239,108,0,.04); }
.upload-card.error { border-color: var(--danger); }
label { min-height: 320px; padding: 32px; display: flex; align-items: center; justify-content: center; flex-direction: column; cursor: pointer; text-align: center; }
input { display: none; }
.file-icon { width: 76px; height: 76px; display: grid; place-items: center; border-radius: 24px; background: var(--soft); color: var(--primary); font-size: 34px; }
.file-icon.ready { background: #e8f5ec; color: var(--success); }
strong { max-width: 90%; margin-top: 22px; overflow: hidden; color: var(--ink); font-size: 23px; text-overflow: ellipsis; white-space: nowrap; }
p { max-width: 640px; margin: 10px 0 0; color: var(--muted); font-size: 13px; line-height: 1.8; }
.choose-button { margin-top: 24px; padding: 11px 26px; border-radius: 999px; background: var(--primary); color: #fff; font-size: 13px; font-weight: 800; }
.choose-button.secondary { border: 1px solid var(--line); background: var(--soft); color: var(--primary); }
.upload-card > button { position: absolute; right: 20px; top: 18px; border: 0; background: transparent; color: var(--muted); cursor: pointer; font-size: 12px; font-weight: 700; }
</style>
