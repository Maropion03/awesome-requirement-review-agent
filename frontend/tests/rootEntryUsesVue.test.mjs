import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const indexSource = readFileSync(resolve(process.cwd(), 'index.html'), 'utf8')

test('root entry mounts the maintained Vue app and has no static-shell redirect', () => {
  assert.match(indexSource, /id="app"/)
  assert.match(indexSource, /src="\/src\/main\.js"/)
  assert.doesNotMatch(indexSource, /single-page-shell/)
  assert.equal(existsSync(resolve(process.cwd(), 'public', 'single-page-shell.html')), false)
})
