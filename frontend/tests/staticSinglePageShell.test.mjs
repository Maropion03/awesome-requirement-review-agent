import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const source = readFileSync(resolve(process.cwd(), 'first page code_integrated.html'), 'utf8')

test('static shell keeps workbench report and assistant in one page', () => {
  assert.match(source, /id="workbenchView"/)
  assert.match(source, /id="reportView"/)
  assert.match(source, /id="assistantView"/)
  assert.match(source, /function switchView\(/)
})

test('static shell avoids page redirects and talks to backend 8005', () => {
  assert.doesNotMatch(source, /window\.location\.href/)
  assert.match(source, /127\.0\.0\.1:8005\/api/)
  assert.match(source, /\/review\/report\//)
  assert.match(source, /\/review\/chat/)
})

test('static shell removes internal implementation labels from the UI copy', () => {
  assert.doesNotMatch(source, /Static Frontend \+ Existing Backend/)
  assert.doesNotMatch(source, /Single Page Shell/)
})
