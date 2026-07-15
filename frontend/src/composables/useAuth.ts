import { ref, computed } from 'vue'
import client from '@/api/client'
import { fetchBillingStatus } from '@/api/billing'

interface User {
  id: number
  email: string
  display_name: string
  account_type?: string
  plan: string
  trial_started_at?: string | null
  trial_expires_at?: string | null
}

const token = ref<string>(localStorage.getItem('gfcri_token') || '')
const user = ref<User | null>(null)
const loading = ref(false)

// Initialize from stored token
if (token.value) {
  try {
    const payload = JSON.parse(atob(token.value.split('.')[0]))
    user.value = {
      id: payload.user_id,
      email: payload.email,
      display_name: '',
      account_type: payload.account_type || 'personal',
      plan: payload.plan,
      trial_expires_at: payload.trial_expires_at || null,
    }
  } catch {}
}

function isTrialCurrentlyActive(u: User | null): boolean {
  if (!u?.trial_expires_at) return false
  const expires = new Date(u.trial_expires_at).getTime()
  return Number.isFinite(expires) && expires > Date.now()
}

function trialDaysRemaining(u: User | null): number {
  if (!isTrialCurrentlyActive(u)) return 0
  const diff = new Date(u!.trial_expires_at!).getTime() - Date.now()
  return Math.max(1, Math.ceil(diff / 86400000))
}

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isTrialActive = computed(() => isTrialCurrentlyActive(user.value))
  const accountType = computed(() => {
    return user.value?.account_type === 'institutional' ? 'institutional' : 'personal'
  })
  const isInstitutionalAccount = computed(() => accountType.value === 'institutional')
  const isPro = computed(() => user.value?.plan === 'pro' || isTrialActive.value || isInstitutionalAccount.value)
  const trialDaysLeft = computed(() => trialDaysRemaining(user.value))
  const effectivePlan = computed(() => {
    if (user.value?.plan === 'pro') return 'pro'
    if (isTrialActive.value) return 'trial'
    return 'free'
  })

  function applyAuthResponse(data: any) {
    token.value = data.token
    user.value = data.user
    localStorage.setItem('gfcri_token', data.token)
    client.defaults.headers.common['Authorization'] = `Bearer ${data.token}`
  }

  async function login(email: string, password: string): Promise<string | null> {
    loading.value = true
    try {
      const res = await client.post('/auth/login', { email, password })
      applyAuthResponse(res.data)
      return null
    } catch (e: any) {
      return e.response?.data?.detail || 'Login failed'
    } finally {
      loading.value = false
    }
  }

  async function register(email: string, password: string, displayName: string): Promise<string | null> {
    loading.value = true
    try {
      const res = await client.post('/auth/register', { email, password, display_name: displayName })
      applyAuthResponse(res.data)
      return null
    } catch (e: any) {
      return e.response?.data?.detail || 'Registration failed'
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('gfcri_token')
    delete client.defaults.headers.common['Authorization']
  }

  function setPro(value: boolean) {
    if (user.value) user.value.plan = value ? 'pro' : 'free'
  }

  function togglePro() {
    setPro(!isPro.value)
  }

  async function startTrial(): Promise<string | null> {
    if (!isLoggedIn.value) return 'AUTH_REQUIRED'
    loading.value = true
    try {
      const res = await client.post('/auth/trial/start')
      applyAuthResponse(res.data)
      return null
    } catch (e: any) {
      return e.response?.data?.detail || 'Unable to start trial'
    } finally {
      loading.value = false
    }
  }

  async function refreshBillingStatus(): Promise<string | null> {
    if (!isLoggedIn.value) return 'AUTH_REQUIRED'
    loading.value = true
    try {
      const data = await fetchBillingStatus()
      if (data.token && data.user) applyAuthResponse(data)
      return null
    } catch (e: any) {
      return e.response?.data?.detail || 'Unable to refresh billing status'
    } finally {
      loading.value = false
    }
  }

  // Set auth header if token exists
  if (token.value) {
    client.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  return {
    user: computed(() => user.value),
    isLoggedIn,
    isPro,
    isTrialActive,
    trialDaysLeft,
    accountType,
    isInstitutionalAccount,
    effectivePlan,
    loading: computed(() => loading.value),
    login,
    register,
    logout,
    startTrial,
    refreshBillingStatus,
    setPro,
    togglePro,
  }
}
