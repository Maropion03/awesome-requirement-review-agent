<template>
  <div class="card">
    <h2>Step 4: 评审报告</h2>

    <div class="summary-row">
      <div><strong>综合评分：</strong>{{ report.score }}/10</div>
      <div><strong>评审建议：</strong>{{ report.suggestion }}</div>
    </div>

    <div>
      <h3>问题清单</h3>
      <ul>
        <li v-for="issue in report.issues" :key="issue.id">
          [{{ issue.level }}] {{ issue.title }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
defineProps({
  report: {
    type: Object,
    default: () => ({
      score: '--',
      suggestion: '尚未生成',
      issues: []
    })
  }
})
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

.summary-row {
  display: grid;
  gap: 6px;
  margin-bottom: 10px;
}

ul {
  margin: 0;
  padding-left: 20px;
}
</style>
