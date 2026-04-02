import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const source = readFileSync(resolve(process.cwd(), 'first page code_integrated.html'), 'utf8')

test('current run card does not include the explanatory annotation', () => {
  assert.doesNotMatch(source, /同一页面内切换工作台、报告和助手视图，不再跳转 URL。/)
})
