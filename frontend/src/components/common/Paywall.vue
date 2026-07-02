<template>
  <div class="relative">
    <div :class="blurred ? 'blur-[6px] select-none pointer-events-none' : ''">
      <slot />
    </div>

    <div v-if="blurred" class="absolute inset-0 flex items-center justify-center bg-[var(--bg)]/60 backdrop-blur-sm rounded-xl z-10">
      <div class="text-center max-w-sm px-6">
        <div class="w-10 h-10 rounded-full bg-[var(--accent)]/10 flex items-center justify-center mx-auto mb-4">
          <span class="text-lg">🔒</span>
        </div>
        <h3 class="text-white font-medium mb-2">{{ title || t('common.upgrade') }}</h3>
        <p class="text-xs text-[var(--muted)] mb-5 leading-relaxed">{{ description || t('common.upgradeDesc') }}</p>
        <p v-if="trialError" class="text-[10px] text-[var(--red)] mb-3">{{ trialError }}</p>
        <button
          @click="handleUpgrade"
          :disabled="loading"
          class="px-5 py-2.5 rounded-lg bg-[var(--accent)] text-white text-sm font-medium hover:bg-[var(--accent)]/90 transition-colors disabled:opacity-50"
        >
          {{ loading ? t('common.loading') : t('trial.start') }}
        </button>
        <p class="text-[10px] text-[var(--muted)]/50 mt-3">{{ t('trial.note') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '@/composables/useI18n'
import { useAuth } from '@/composables/useAuth'

const { t, tx } = useI18n()
const { isLoggedIn, startTrial, loading } = useAuth()
const router = useRouter()
const trialError = ref('')

defineProps<{
  blurred: boolean
  title?: string
  description?: string
}>()

const emit = defineEmits(['upgrade'])

async function handleUpgrade() {
  trialError.value = ''
  emit('upgrade')
  if (!isLoggedIn.value) {
    router.push({ path: '/auth', query: { trial: '1' } })
    return
  }
  const err = await startTrial()
  if (err) trialError.value = err === 'Trial already used' ? t('trial.used') : tx(err)
}
</script>
