<template>
  <div class="card">
    <h2>Step 1: 上传 PRD 文档</h2>
    <p class="desc">支持 .md / .docx，先做低保真占位交互。</p>

    <label
      class="dropzone"
      :class="{ dragging: isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <input type="file" class="file-input" accept=".md,.docx" @change="handleFileChange" />
      <span>拖拽文件到此区域，或点击选择文件</span>
    </label>

    <p v-if="modelValue" class="filename">已选择：{{ modelValue }}</p>
    <p v-else class="placeholder">尚未选择文件</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])
const isDragging = ref(false)

function emitFile(file) {
  if (!file) return
  emit('update:modelValue', file.name)
}

function handleFileChange(event) {
  const file = event.target.files?.[0]
  emitFile(file)
}

function handleDrop(event) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  emitFile(file)
}
</script>

<style scoped>
.card {
  background: #fff;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  padding: 16px;
}

h2 {
  margin: 0 0 8px;
  font-size: 18px;
}

.desc {
  color: #64748b;
  margin-bottom: 12px;
}

.dropzone {
  border: 2px dashed #94a3b8;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #334155;
  cursor: pointer;
  transition: 0.2s ease;
  text-align: center;
  padding: 12px;
}

.dropzone.dragging {
  border-color: #2563eb;
  background: #eff6ff;
}

.file-input {
  display: none;
}

.filename {
  margin-top: 12px;
  color: #1e293b;
  font-weight: 600;
}

.placeholder {
  margin-top: 12px;
  color: #94a3b8;
}
</style>
