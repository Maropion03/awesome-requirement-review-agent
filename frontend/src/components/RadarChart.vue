<template>
  <div class="radar-wrap" aria-label="六维评审雷达图">
    <svg viewBox="0 0 320 300" role="img">
      <polygon v-for="level in 5" :key="level" :points="gridPoints(level / 5)" class="grid-ring" />
      <line v-for="point in outerPoints" :key="`${point.x}-${point.y}`" :x1="center.x" :y1="center.y" :x2="point.x" :y2="point.y" class="axis" />
      <polygon v-if="plotPoints" :points="plotPoints" class="score-area" />
      <circle v-for="(point, index) in scoredPoints" :key="index" :cx="point.x" :cy="point.y" r="3.8" class="score-dot" />
      <text v-for="(label, index) in labels" :key="label" :x="labelPoints[index].x" :y="labelPoints[index].y" :text-anchor="labelPoints[index].anchor" dominant-baseline="middle">{{ label }}</text>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ dimensions: { type: Array, default: () => [] } })
const center = { x: 160, y: 145 }
const radius = 92
const fallbackLabels = ['需求完整性', '需求合理性', '用户价值', '技术可行性', '实现风险', '优先级一致性']
const labels = computed(() => fallbackLabels.map((fallback, index) => props.dimensions[index]?.dimension || fallback))

function pointAt(index, scale = 1) {
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / 6
  return { x: center.x + Math.cos(angle) * radius * scale, y: center.y + Math.sin(angle) * radius * scale }
}

const outerPoints = computed(() => fallbackLabels.map((_, index) => pointAt(index)))
const scoredPoints = computed(() => fallbackLabels.map((_, index) => {
  const score = Math.max(0, Math.min(10, Number(props.dimensions[index]?.score) || 0))
  return pointAt(index, score / 10)
}))
const plotPoints = computed(() => scoredPoints.value.map((point) => `${point.x},${point.y}`).join(' '))
const labelPoints = computed(() => fallbackLabels.map((_, index) => {
  const point = pointAt(index, 1.25)
  const dx = point.x - center.x
  return { ...point, anchor: Math.abs(dx) < 8 ? 'middle' : dx > 0 ? 'start' : 'end' }
}))

function gridPoints(scale) {
  return fallbackLabels.map((_, index) => {
    const point = pointAt(index, scale)
    return `${point.x},${point.y}`
  }).join(' ')
}
</script>

<style scoped>
.radar-wrap { width: 100%; height: 280px; display: grid; place-items: center; }
svg { width: 100%; height: 100%; overflow: visible; }
.grid-ring { fill: none; stroke: var(--line); stroke-width: 1; }
.axis { stroke: var(--line); stroke-width: 1; }
.score-area { fill: rgb(239 108 0 / 20%); stroke: var(--primary); stroke-width: 2.5; }
.score-dot { fill: var(--primary); stroke: #fffdf8; stroke-width: 2; }
text { fill: var(--muted); font-size: 10px; font-weight: 700; }
</style>
