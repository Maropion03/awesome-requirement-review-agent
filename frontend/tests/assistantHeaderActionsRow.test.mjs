import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const source = readFileSync(resolve(process.cwd(), 'first page code_integrated.html'), 'utf8')

test('assistant header actions stay on one row', () => {
  assert.match(source, /assistantActionsRow/)
  assert.match(source, /id="assistantActionsRow" class="[^"]*flex-nowrap[^"]*overflow-x-auto[^"]*"/)
  assert.match(source, /id="assistantShareBtn" class="[^"]*whitespace-nowrap[^"]*"/)
  assert.match(source, /id="assistantExportBtn" class="[^"]*whitespace-nowrap[^"]*"/)
  assert.match(source, /id="assistantRerunBtn" class="[^"]*whitespace-nowrap[^"]*"/)
})
