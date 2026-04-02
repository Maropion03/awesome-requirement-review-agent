import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const source = readFileSync(resolve(process.cwd(), 'first page code_integrated.html'), 'utf8')

test('static shell adapts total score display between /10 and /100', () => {
  assert.match(source, /function getTotalScoreMeta\(/)
  assert.match(source, /id="totalScoreMaxLabel"/)
  assert.match(source, /scoreMeta\.max/)
  assert.match(source, /numeric <= 10/)
})
