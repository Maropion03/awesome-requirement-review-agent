import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const source = readFileSync(resolve(process.cwd(), 'first page code_integrated.html'), 'utf8')

test('workbench removes the top summary cards block', () => {
  assert.doesNotMatch(source, /id="fileMetaCard"/)
  assert.doesNotMatch(source, /id="reviewModeCard"/)
  assert.doesNotMatch(source, /id="reportStateCard"/)
  assert.doesNotMatch(source, /id="issueStateCard"/)
})
