<template>
  <section class="card upload-card">
    <div class="section-head">
      <div>
        <h2>上传 PRD 文档</h2>
        <p class="desc">支持 Markdown 或 Word 文档，上传完成后即可启动一次完整评审。</p>
      </div>
      <button
        v-if="modelValue"
        class="ghost-button"
        type="button"
        :disabled="disabled"
        @click="clearSelection"
      >
        清空
      </button>
    </div>

    <label
      class="dropzone"
      :class="[statusClass, { dragging: isDragging, disabled }]"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="handleDrop"
    >
      <input
        type="file"
        class="file-input"
        accept=".md,.docx"
        :disabled="disabled"
        @change="handleFileChange"
      />
      <span class="drop-title">
        {{ modelValue ? '替换当前文档' : '拖拽文件到此区域，或点击选择文件' }}
      </span>
      <span class="drop-copy">支持 `.md`、`.docx`，建议文件大小不超过 10MB</span>
    </label>

    <div class="upload-meta">
      <div class="meta-copy">
        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
        <p v-else-if="modelValue" class="filename">当前文件：{{ modelValue }}</p>
        <p v-else class="placeholder">尚未选择文件</p>
      </div>
      <span class="status-pill" :class="statusClass">{{ statusLabel }}</span>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  status: {
    type: String,
    default: 'idle',
  },
  errorMessage: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'file-selected', 'clear-file'])
const isDragging = ref(false)

const statusLabel = computed(() => {
  const labels = {
    idle: '等待上传',
    ready: '已选择',
    uploading: '上传中',
    uploaded: '已上传',
    error: '上传异常',
  }

  return labels[props.status] || '等待上传'
})

const statusClass = computed(() => props.status || 'idle')

function emitFile(file) {
  if (!file || props.disabled) return
  emit('update:modelValue', file.name)
  emit('file-selected', file)
}

function clearSelection() {
  emit('update:modelValue', '')
  emit('clear-file')
}

function onDragOver() {
  if (props.disabled) return
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function handleFileChange(event) {
  const file = event.target.files?.[0]
  emitFile(file)
}

function handleDrop(event) {
  isDragging.value = false
  if (props.disabled) return
  const file = event.dataTransfer?.files?.[0]
  emitFile(file)
}
</script>

<style scoped>
.card {
  background: #ffffff;
  border: 1px solid transparent;
  border-radius: 1rem;
  padding: 16px;
  box-shadow: 0 4px 6px rgba(31, 24, 23, 0.06);
}

.upload-card {
  display: grid;
  gap: 14px;
}

.section-head,
.upload-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

h2,
p {
  margin: 0;
}

h2 {
  font-family: 'Satoshi', sans-serif;
  font-size: 1.125rem;
  color: #1d1b17;
}

.desc,
.placeholder,
.drop-copy {
  color: #64748b;
}

.desc,
.filename,
.placeholder,
.error-text,
.drop-copy,
.drop-title,
.ghost-button,
.status-pill {
  font-family: 'Inter', sans-serif;
}

.desc {
  margin-top: 4px;
  font-size: 0.875rem;
  line-height: 1.5;
}

.dropzone {
  border: 1.5px dashed #c7d3e3;
  min-height: 160px;
  display: grid;
  gap: 8px;
  place-content: center;
  border-radius: 1rem;
  color: #334155;
  cursor: pointer;
  transition: 0.2s ease;
  text-align: center;
  padding: 16px;
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.65), rgba(255, 255, 255, 0.95)),
    #ffffff;
}

.dropzone.ready,
.dropzone.uploaded {
  border-color: #8bb3f2;
}

.dropzone.uploading {
  border-color: #f59e0b;
}

.dropzone.error {
  border-color: #dc2626;
  background: #fff7f7;
}

.dropzone.dragging {
  border-color: #3a2e47;
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(58, 46, 71, 0.08);
}

.dropzone.disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.drop-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1d1b17;
}

.drop-copy {
  font-size: 0.8125rem;
}

.file-input {
  display: none;
}

.filename,
.placeholder,
.error-text {
  font-size: 0.875rem;
}

.filename {
  color: #1e293b;
  font-weight: 600;
}

.error-text {
  color: #b91c1c;
}

.meta-copy {
  display: grid;
  gap: 4px;
}

.status-pill {
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid transparent;
  white-space: nowrap;
}

.status-pill.idle {
  background: #f8fafc;
  color: #64748b;
}

.status-pill.ready,
.status-pill.uploaded {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

.status-pill.uploading {
  background: #fffbeb;
  color: #b45309;
  border-color: #fcd34d;
}

.status-pill.error {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fca5a5;
}

.ghost-button {
  border: 1px solid #d8e1ef;
  border-radius: 999px;
  background: #ffffff;
  color: #4a5568;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 0.8125rem;
}

.ghost-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 720px) {
  .section-head,
  .upload-meta {
    flex-direction: column;
    align-items: stretch;
  }

  .status-pill {
    width: fit-content;
  }
}
</style>
