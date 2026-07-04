<template>
  <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 lg:p-5 card-hover">
    <div class="flex flex-col gap-3">
      <div>
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[3px]">{{ t('forward.alertSub') }}</p>
        <h3 class="mt-1 text-sm font-medium text-white">{{ t('alertSub.title') }}</h3>
        <p class="terminal-copy mt-2">{{ t('forward.alertDesc') }}</p>
      </div>
      <div v-if="!subscribed" class="flex gap-2">
        <input
          v-model="alertEmail"
          type="email"
          :placeholder="t('alertSub.placeholder')"
          class="min-w-0 flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-xs text-white focus:border-[var(--accent)] focus:outline-none"
        />
        <button
          class="rounded-lg bg-[var(--accent)] px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-[var(--accent)]/80"
          type="button"
          @click="subscribe"
        >
          {{ t('common.subscribe') }}
        </button>
      </div>
      <p v-else class="text-xs text-[var(--green)]">✓ {{ t('forward.subscribed') }} {{ alertEmail }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()
const alertEmail = ref(localStorage.getItem('gfcri_alert_email') || '')
const subscribed = ref(!!localStorage.getItem('gfcri_alert_email'))

function subscribe() {
  if (alertEmail.value && alertEmail.value.includes('@')) {
    localStorage.setItem('gfcri_alert_email', alertEmail.value)
    subscribed.value = true
  }
}
</script>
