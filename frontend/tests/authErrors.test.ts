import assert from 'node:assert/strict'
import test from 'node:test'

import { formatAuthError } from '../src/composables/authErrors.ts'

test('maps invalid credentials to a localized message', () => {
  const error = {
    response: {
      status: 401,
      data: { detail: { code: 'AUTH_INVALID_CREDENTIALS' } },
    },
  }

  assert.equal(formatAuthError(error, 'zh', 'Login failed'), '邮箱或密码错误')
  assert.equal(formatAuthError(error, 'en', 'Login failed'), 'Invalid email or password')
})

test('extracts FastAPI validation details', () => {
  const error = {
    response: {
      status: 422,
      data: { detail: [{ msg: 'String should have at least 6 characters' }] },
    },
  }

  assert.equal(
    formatAuthError(error, 'en', 'Registration failed'),
    'String should have at least 6 characters',
  )
})

test('returns a useful network failure message', () => {
  const error = { request: {}, message: 'Network Error' }

  assert.equal(
    formatAuthError(error, 'zh', 'Login failed'),
    '无法连接服务器，请检查网络后重试',
  )
})
