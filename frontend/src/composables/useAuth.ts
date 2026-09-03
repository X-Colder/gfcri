import { ref, computed } from 'vue'
import client from '@/api/client'
import { fetchBillingStatus } from '@/api/billing'

interface Membership {
  organization_id: number
  org_key: string
  name: string
  role: string
}

interface User {
  id: number
  email: string
  display_name: string
  account_type?: string
  plan: string
  access_level?: string
  institutional_access?: boolean
  institutional_memberships?: Membership[]
  entitlements?: string[]
  trial_started_at?: string | null
  trial_expires_at?: string | null
}

const token = ref<string>(localStorage.getItem('gfcri_token') || '')
const user = ref<User | null>(null)
const loading = ref(false)
const sessionReady = ref(!token.value)
let hydrationStarted = false

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

function clearAuth() {
  token.value = ''
  user.value = null
  localStorage.removeItem('gfcri_token')
  delete client.defaults.headers.common['Authorization']
}

function applyAuthResponse(data: any) {
  token.value = data.token
  user.value = data.user
  localStorage.setItem('gfcri_token', data.token)
  client.defaults.headers.common['Authorization'] = `Bearer ${data.token}`
}

async function hydrateSession() {
  if (!token.value || hydrationStarted) return
  hydrationStarted = true
  client.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  try {
    const res = await client.get('/auth/me')
    user.value = res.data
  } catch {
    clearAuth()
  } finally {
    sessionReady.value = true
  }
}

if (token.value) {
  void hydrateSession()
}

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isTrialActive = computed(() => isTrialCurrentlyActive(user.value))
  const accountType = computed(() => {
    return user.value?.account_type === 'institutional' ? 'institutional' : 'personal'
  })
  const isInstitutionalAccount = computed(() => Boolean(
    user.value?.institutional_access
      || user.value?.account_type === 'institutional'
      || user.value?.institutional_memberships?.length,
  ))
  const hasEntitlement = (key: string) => Boolean(user.value?.entitlements?.includes(key))
  const isPro = computed(() => hasEntitlement('deep_analysis'))
  const trialDaysLeft = computed(() => trialDaysRemaining(user.value))
  const effectivePlan = computed(() => {
    if (isInstitutionalAccount.value) return 'institutional'
    if (user.value?.plan === 'pro') return 'pro'
    if (isTrialActive.value) return 'trial'
    return 'free'
  })

  async function login(email: string, password: string): Promise<string | null> {
    loading.value = true
    try {
      const res = await client.post('/auth/login', { email, password })
      applyAuthResponse(res.data)
      sessionReady.value = true
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
      sessionReady.value = true
      return null
    } catch (e: any) {
      return e.response?.data?.detail || 'Registration failed'
    } finally {
      loading.value = false
    }
  }

  function logout() {
    clearAuth()
    sessionReady.value = true
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

  return {
    user: computed(() => user.value),
    isLoggedIn,
    isPro,
    isTrialActive,
    trialDaysLeft,
    accountType,
    isInstitutionalAccount,
    effectivePlan,
    hasEntitlement,
    sessionReady: computed(() => sessionReady.value),
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
