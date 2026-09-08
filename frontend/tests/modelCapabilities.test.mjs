import test from 'node:test'
import assert from 'node:assert/strict'

import { detectModelCapability, isKnownTextOnlyModel, shouldConfirmTextOnlyPdfReview } from '../src/lib/modelCapabilities.js'

test('detects the officially documented GLM-5.3 text-only family', () => {
  assert.equal(isKnownTextOnlyModel('glm-5.3'), true)
  assert.equal(isKnownTextOnlyModel('GLM-5.3-Flash'), true)
  assert.equal(detectModelCapability('glm-5.3').capability, 'text_only')
})

test('unknown and vision model names are not guessed as text-only', () => {
  assert.equal(isKnownTextOnlyModel('glm-4.6v-flash'), false)
  assert.equal(isKnownTextOnlyModel('my-private-model'), false)
  assert.equal(detectModelCapability('').capability, 'unknown')
})

test('asks for confirmation only when a PDF uses a known text-only review model', () => {
  assert.equal(shouldConfirmTextOnlyPdfReview({ fileName: 'review.pdf', model: 'glm-5.3' }), true)
  assert.equal(shouldConfirmTextOnlyPdfReview({ fileName: 'review.md', model: 'glm-5.3' }), false)
  assert.equal(shouldConfirmTextOnlyPdfReview({ fileName: 'review.pdf', model: 'glm-4.6v-flash' }), false)
})
