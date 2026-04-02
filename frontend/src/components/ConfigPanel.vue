<template>
  <section class="card config-card">
    <div class="section-head">
      <div>
        <h2>评审配置</h2>
        <p class="desc">选择本次评审的审查强度。不同预设会影响提示词权重和问题倾向。</p>
      </div>
      <span class="mode-chip">{{ presetLabel }}</span>
    </div>

    <div class="row">
      <label for="preset">预设模式</label>
      <select id="preset" :value="modelValue" @change="emit('update:modelValue', $event.target.value)">
        <option value="normal">标准评审</option>
        <option value="p0_critical">高风险发布</option>
        <option value="innovation">创新探索</option>
      </select>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'normal',
  },
})

const emit = defineEmits(['update:modelValue'])

const presetLabel = computed(() => {
  const labels = {
    normal: '标准评审',
    p0_critical: '高风险发布',
    innovation: '创新探索',
  }

  return labels[props.modelValue] || '标准评审'
})
</script>

<style scoped>
.card {
  background: #ffffff;
  border: 1px solid transparent;
  border-radius: 1rem;
  padding: 16px;
  box-shadow: 0 4px 6px rgba(31, 24, 23, 0.06);
}

.config-card {
  display: grid;
  gap: 14px;
}

.section-head {
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
.row,
label,
select,
.mode-chip {
  font-family: 'Inter', sans-serif;
}

.desc {
  margin-top: 4px;
  color: #64748b;
  font-size: 0.875rem;
  line-height: 1.5;
}

.row {
  display: grid;
  gap: 8px;
}

label {
  color: #334155;
  font-size: 0.875rem;
  font-weight: 600;
}

select {
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 0.9rem;
  background: #ffffff;
  color: #1f2937;
  font-size: 0.9375rem;
}

.mode-chip {
  border-radius: 999px;
  padding: 7px 12px;
  background: #f3eef8;
  color: #4b2f68;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

@media (max-width: 720px) {
  .section-head {
    flex-direction: column;
  }

  .mode-chip {
    width: fit-content;
  }
}
</style>
