import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const indexSource = readFileSync(resolve(process.cwd(), 'index.html'), 'utf8')

test('root entry redirects to the integrated static shell', () => {
  assert.match(indexSource, /single-page-shell\.html/)
  assert.ok(existsSync(resolve(process.cwd(), 'public', 'single-page-shell.html')))
})
