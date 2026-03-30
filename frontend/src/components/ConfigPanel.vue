<template>
  <div class="card">
    <h2>Step 2: 评审配置</h2>
    <div class="row">
      <label for="preset">Preset</label>
      <select id="preset" :value="modelValue" @change="emit('update:modelValue', $event.target.value)">
        <option value="normal">normal</option>
        <option value="p0_critical">p0_critical</option>
        <option value="innovation">innovation</option>
      </select>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: 'normal'
  }
})

const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
.card {
  background: #fff;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  padding: 16px;
}

h2 {
  margin: 0 0 12px;
  font-size: 18px;
}

.row {
  display: flex;
  align-items: center;
  gap: 12px;
}

select {
  padding: 8px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
</style>
