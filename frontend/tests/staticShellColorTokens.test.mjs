import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const source = readFileSync(resolve(process.cwd(), 'first page code_integrated.html'), 'utf8')

test('static shell uses an orange primary tone while keeping success states green', () => {
  assert.match(source, /primary:\s*"#ef6c00"/)
  assert.match(source, /success:\s*"#256f4b"/)
  assert.match(source, /bg-emerald-500/)
  assert.match(source, /text-emerald-300/)
})

test('static shell renders primary titles in black', () => {
  assert.match(source, /<h1 class="[^"]*text-ink[^"]*">PRD 评审工作台<\/h1>/)
  assert.match(source, /<h2 id="pageTitle" class="[^"]*text-ink[^"]*">新建 PRD 评审任务<\/h2>/)
})

test('static shell keeps a consistent panel background under every page view', () => {
  assert.match(source, /\.content-shell\s*\{[\s\S]*background:\s*rgba\(255,\s*253,\s*248,\s*0\.72\)/)
  assert.match(source, /<main class="content-shell [^"]*">/)
})
