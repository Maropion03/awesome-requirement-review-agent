import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createAgentStages,
  applyStreamingMessage,
  applyDimensionEvent,
  completeReporterStage,
} from '../src/lib/agentStages.js'

test('streaming messages activate orchestrator and reporter stages', () => {
  let stages = createAgentStages()

  stages = applyStreamingMessage(stages, 'Orchestrator Agent 已接管评审流程。')
  assert.equal(stages[0].status, 'active')
  assert.equal(stages[1].status, 'pending')

  stages = applyStreamingMessage(stages, 'Reporter Agent 正在汇总最终报告...')
  assert.equal(stages[0].status, 'complete')
  assert.equal(stages[2].status, 'active')
})

test('dimension events activate and complete reviewer stage with current dimension', () => {
  let stages = createAgentStages()

  stages = applyDimensionEvent(stages, 'start', '需求完整性')
  assert.equal(stages[1].status, 'active')
  assert.equal(stages[1].detail, '当前维度：需求完整性')

  stages = applyDimensionEvent(stages, 'complete', '需求完整性')
  assert.equal(stages[1].status, 'active')
  assert.equal(stages[1].detail, '已完成：需求完整性')
})

test('completeReporterStage marks all agent stages complete', () => {
  const stages = completeReporterStage(createAgentStages())
  assert.deepEqual(
    stages.map((stage) => stage.status),
    ['complete', 'complete', 'complete'],
  )
})
