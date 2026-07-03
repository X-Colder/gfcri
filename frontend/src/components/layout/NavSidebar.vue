<template>
  <aside class="w-56 shrink-0 bg-[var(--card)] border-r border-[var(--border)] flex flex-col">
    <div class="p-5 border-b border-[var(--border)]">
      <h1 class="text-xl font-extralight tracking-wide text-white">GFCRI</h1>
      <p class="text-[10px] text-[var(--muted)] mt-1 uppercase tracking-[3px]">{{ modeLabel }}</p>
      <div class="mt-4 grid grid-cols-2 gap-1 rounded-lg border border-[var(--border)] bg-black/10 p-1">
        <button
          class="rounded-md px-2 py-1.5 text-[10px] transition-colors"
          :class="mode === 'global' ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'text-[var(--muted)] hover:text-white'"
          @click="setMode('global')"
        >
          Global
        </button>
        <button
          class="rounded-md px-2 py-1.5 text-[10px] transition-colors"
          :class="mode === 'institutional' ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'text-[var(--muted)] hover:text-white'"
          @click="setMode('institutional')"
        >
          Institution
        </button>
      </div>
    </div>
    <nav class="flex-1 p-3 space-y-0.5">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200"
        :class="[
          $route.path === item.path
            ? 'bg-white/[0.04] text-white border-l-2 border-[var(--accent)] pl-[10px]'
            : 'text-[var(--muted)] hover:text-white hover:bg-white/[0.03]'
        ]"
      >
        <span class="text-sm opacity-70">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="p-4 border-t border-[var(--border)] space-y-3">
      <!-- User section -->
      <div v-if="isLoggedIn" class="flex items-center justify-between">
        <div class="flex items-center gap-2 min-w-0">
          <div class="w-6 h-6 rounded-full bg-[var(--accent)]/20 flex items-center justify-center text-xs text-[var(--accent)]">
            {{ user?.display_name?.[0] || user?.email?.[0] || '?' }}
          </div>
          <div class="min-w-0">
            <span class="block text-xs text-[var(--muted)] truncate">{{ user?.display_name || user?.email }}</span>
            <span class="text-[9px]" :class="isPro ? 'text-[var(--accent)]' : 'text-[var(--muted)]/60'">
              {{ planLabel }}
            </span>
          </div>
        </div>
        <button @click="logout" class="text-[9px] text-[var(--muted)] hover:text-white">{{ t('auth.logout') }}</button>
      </div>
      <router-link v-else to="/auth"
                   class="block w-full text-center px-3 py-2 rounded-lg text-xs bg-[var(--accent)]/10 text-[var(--accent)] hover:bg-[var(--accent)]/20 transition-colors">
        {{ t('auth.login') }} / {{ t('auth.register') }}
      </router-link>

      <!-- Language toggle -->
      <button @click="toggleLang"
              class="w-full flex items-center justify-between px-3 py-1.5 rounded text-[10px] text-[var(--muted)] hover:text-white transition-colors">
        <span>🌐 {{ lang === 'zh' ? '中文' : 'English' }}</span>
        <span class="opacity-40">{{ lang === 'zh' ? 'EN' : '中' }}</span>
      </button>

      <p class="text-[10px] text-[var(--muted)]/40 leading-relaxed">
        38 indicators · 12 chains<br/>Updated daily 06:00 UTC
      </p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'
import { useProductMode } from '@/composables/useProductMode'

const { user, isLoggedIn, isPro, effectivePlan, trialDaysLeft, logout } = useAuth()
const { t, lang, toggleLang } = useI18n()
const { mode, isInstitutional, setMode } = useProductMode()

const planLabel = computed(() => {
  if (effectivePlan.value === 'pro') return t('plan.pro')
  if (effectivePlan.value === 'trial') return t('plan.trial', { days: trialDaysLeft.value })
  return t('plan.free')
})

const modeLabel = computed(() =>
  isInstitutional.value ? t('product.institutionalMode') : t('product.globalMode')
)

const navItems = computed(() => {
  const base = [
    { path: '/', icon: '◉', label: t('nav.dashboard') },
    { path: '/analysis', icon: '◈', label: t('nav.analysis') },
    { path: '/forward', icon: '⚡', label: t('nav.forward') },
    { path: '/backtest', icon: '⏱', label: t('nav.backtest') },
  ]
  if (isInstitutional.value) {
    base.splice(1, 0, { path: '/institutional', icon: '▣', label: t('nav.institutional') })
  }
  base.push({ path: '/methodology', icon: '◇', label: t('nav.methodology') })
  return base
})
</script>
