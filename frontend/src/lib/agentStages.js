const baseStages = [
  {
    id: 'orchestrator',
    title: 'Orchestrator Agent',
    description: '拆解任务、分配维度并协调整条评审链路。',
    status: 'pending',
    detail: '等待接管评审流程',
  },
  {
    id: 'reviewers',
    title: 'Reviewer Agents',
    description: '按维度逐个分析 PRD 并产出问题。',
    status: 'pending',
    detail: '等待开始维度评审',
  },
  {
    id: 'reporter',
    title: 'Reporter Agent',
    description: '汇总各维度结论并生成最终报告。',
    status: 'pending',
    detail: '等待汇总结果',
  },
]

export function createAgentStages() {
  return baseStages.map((stage) => ({ ...stage }))
}

export function applyStreamingMessage(stages, message) {
  if (message.includes('Orchestrator Agent')) {
    return stages.map((stage) => {
      if (stage.id === 'orchestrator') {
        return { ...stage, status: 'active', detail: '正在协调评审任务' }
      }
      return stage
    })
  }

  if (message.includes('Reporter Agent')) {
    return stages.map((stage) => {
      if (stage.id === 'orchestrator') {
        return { ...stage, status: 'complete', detail: '协调完成' }
      }
      if (stage.id === 'reviewers' && stage.status !== 'complete') {
        return { ...stage, status: 'complete', detail: stage.detail || '维度评审完成' }
      }
      if (stage.id === 'reporter') {
        return { ...stage, status: 'active', detail: '正在汇总最终报告' }
      }
      return stage
    })
  }

  return stages
}

export function applyDimensionEvent(stages, eventType, dimensionName) {
  return stages.map((stage) => {
    if (stage.id === 'orchestrator' && eventType === 'start') {
      return { ...stage, status: 'complete', detail: '任务已分配给 Reviewer Agents' }
    }

    if (stage.id !== 'reviewers') return stage

    if (eventType === 'start') {
      return { ...stage, status: 'active', detail: `当前维度：${dimensionName}` }
    }

    if (eventType === 'complete') {
      return { ...stage, status: 'active', detail: `已完成：${dimensionName}` }
    }

    return stage
  })
}

export function completeReporterStage(stages) {
  return stages.map((stage) => ({
    ...stage,
    status: 'complete',
    detail: stage.id === 'reporter' ? '最终报告已生成' : stage.detail,
  }))
}
