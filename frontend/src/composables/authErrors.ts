export type AuthLanguage = 'zh' | 'en'

type ErrorLike = {
  response?: {
    status?: number
    data?: {
      detail?: unknown
    }
  }
  request?: unknown
  message?: string
}

const localizedMessages: Record<string, Record<AuthLanguage, string>> = {
  AUTH_INVALID_CREDENTIALS: {
    zh: '邮箱或密码错误',
    en: 'Invalid email or password',
  },
  AUTH_ACCOUNT_LOCKED: {
    zh: '登录失败次数过多，账户暂时锁定，请稍后再试',
    en: 'Too many failed attempts. Your account is temporarily locked.',
  },
  AUTH_ACCOUNT_INACTIVE: {
    zh: '账户已停用，请联系管理员',
    en: 'Your account is inactive. Please contact an administrator.',
  },
  AUTH_REQUIRED: {
    zh: '请先登录',
    en: 'Please log in first.',
  },
  EMAIL_ALREADY_REGISTERED: {
    zh: '该邮箱已经注册，请直接登录',
    en: 'This email is already registered. Please log in.',
  },
}

function localizedCode(code: unknown, language: AuthLanguage): string | null {
  const messages = localizedMessages[String(code || '')]
  return messages?.[language] || null
}

function legacyMessage(detail: string, language: AuthLanguage): string {
  const normalized = detail.trim().toLowerCase()
  if (normalized === 'invalid email or password') {
    return localizedMessages.AUTH_INVALID_CREDENTIALS[language]
  }
  if (normalized === 'account temporarily locked') {
    return localizedMessages.AUTH_ACCOUNT_LOCKED[language]
  }
  if (normalized === 'email already registered') {
    return localizedMessages.EMAIL_ALREADY_REGISTERED[language]
  }
  return detail
}

export function formatAuthError(
  error: unknown,
  language: AuthLanguage,
  fallback: string,
): string {
  const candidate = (error || {}) as ErrorLike
  const detail = candidate.response?.data?.detail

  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    const structured = detail as { code?: string; message?: string }
    const codeMessage = localizedCode(structured.code, language)
    if (codeMessage) return codeMessage
    if (structured.message) return structured.message
  }

  if (Array.isArray(detail)) {
    const first = detail.find((item) => item && typeof item.msg === 'string')
    if (first?.msg) return first.msg
  }

  if (typeof detail === 'string' && detail.trim()) {
    return legacyMessage(detail, language)
  }

  if (!candidate.response && (candidate.request || candidate.message === 'Network Error')) {
    return language === 'zh'
      ? '无法连接服务器，请检查网络后重试'
      : 'Unable to connect to the server. Check your network and try again.'
  }

  if (candidate.response?.status === 401) {
    return localizedMessages.AUTH_INVALID_CREDENTIALS[language]
  }
  if (candidate.response?.status === 429) {
    return localizedMessages.AUTH_ACCOUNT_LOCKED[language]
  }

  return fallback
}
