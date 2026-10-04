import assert from 'node:assert/strict'
import test from 'node:test'

import {
  messageForHttpStatus,
  NETWORK_ERROR_MESSAGE,
} from './apiErrors.ts'

test('network errors are distinct from HTTP responses', () => {
  assert.match(NETWORK_ERROR_MESSAGE, /could not connect/)
  assert.notEqual(NETWORK_ERROR_MESSAGE, messageForHttpStatus(503))
})

test('common client errors receive actionable messages', () => {
  assert.match(messageForHttpStatus(400), /review the information/)
  assert.match(messageForHttpStatus(404), /could not be found/)
  assert.match(messageForHttpStatus(409), /conflicts/)
  assert.match(messageForHttpStatus(422), /form/)
  assert.match(messageForHttpStatus(418), /could not accept/)
})

test('server errors do not expose response details', () => {
  for (const status of [500, 502, 503, 504, 599]) {
    assert.match(messageForHttpStatus(status), /server problem|temporarily unavailable/)
    assert.doesNotMatch(
      messageForHttpStatus(status),
      /mongodb|password|connection string/i,
    )
  }
})
