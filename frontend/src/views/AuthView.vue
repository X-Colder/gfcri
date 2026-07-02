<template>
  <div class="min-h-screen flex items-center justify-center" style="background:var(--bg)">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="text-center mb-10">
        <h1 class="text-2xl font-extralight tracking-wide text-white">GFCRI</h1>
        <p class="text-[10px] text-[var(--muted)] uppercase tracking-[3px] mt-1">Global Risk Index</p>
      </div>

      <!-- Card -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-8">
        <h2 class="text-lg font-light text-white mb-6 text-center">
          {{ wantsTrial ? t('trial.authTitle') : (isLogin ? t('auth.login') : t('auth.register')) }}
        </h2>
        <p v-if="wantsTrial" class="text-xs text-[var(--muted)] text-center mb-5 leading-relaxed">
          {{ t('trial.authDesc') }}
        </p>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div v-if="!isLogin">
            <label class="text-xs text-[var(--muted)] mb-1 block">{{ t('auth.name') }}</label>
            <input v-model="displayName" type="text"
                   class="w-full px-4 py-2.5 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-white text-sm focus:border-[var(--accent)] focus:outline-none" />
          </div>
          <div>
            <label class="text-xs text-[var(--muted)] mb-1 block">{{ t('auth.email') }}</label>
            <input v-model="email" type="email" required
                   class="w-full px-4 py-2.5 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-white text-sm focus:border-[var(--accent)] focus:outline-none" />
          </div>
          <div>
            <label class="text-xs text-[var(--muted)] mb-1 block">{{ t('auth.password') }}</label>
            <input v-model="password" type="password" required minlength="6"
                   class="w-full px-4 py-2.5 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-white text-sm focus:border-[var(--accent)] focus:outline-none" />
          </div>

          <p v-if="error" class="text-xs text-[var(--red)]">{{ error }}</p>

          <button type="submit" :disabled="authLoading"
                  class="w-full py-2.5 rounded-lg bg-[var(--accent)] text-white text-sm font-medium hover:bg-[var(--accent)]/80 transition-colors disabled:opacity-50">
            {{ authLoading ? '...' : (isLogin ? t('auth.login') : t('auth.register')) }}
          </button>
        </form>

        <p class="text-center mt-5 text-xs text-[var(--muted)]">
          {{ isLogin ? t('auth.noAccount') : t('auth.hasAccount') }}
          <button @click="isLogin = !isLogin" class="text-[var(--accent)] hover:text-white ml-1">
            {{ isLogin ? t('auth.register') : t('auth.login') }}
          </button>
        </p>
      </div>

      <!-- Language toggle -->
      <div class="text-center mt-4">
        <button @click="toggleLang" class="text-xs text-[var(--muted)] hover:text-white transition-colors">
          {{ lang === 'zh' ? 'English' : '中文' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'

const router = useRouter()
const route = useRoute()
const { login, register, startTrial, loading: authLoading } = useAuth()
const { t, tx, lang, toggleLang } = useI18n()

const isLogin = ref(true)
const email = ref('')
const password = ref('')
const displayName = ref('')
const error = ref('')
const wantsTrial = computed(() => route.query.trial === '1')

async function handleSubmit() {
  error.value = ''
  let err: string | null
  if (isLogin.value) {
    err = await login(email.value, password.value)
  } else {
    err = await register(email.value, password.value, displayName.value)
  }
  if (err) {
    error.value = err
  } else {
    if (wantsTrial.value) {
      const trialErr = await startTrial()
      if (trialErr && trialErr !== 'Trial already used') {
        error.value = tx(trialErr)
        return
      }
    }
    router.push('/')
  }
}
</script>
