<template>
  <div class="mb-8 fade-in" v-if="chains.length">
    <div class="flex items-center justify-between mb-3 cursor-pointer" @click="expanded = !expanded">
      <div class="flex items-center gap-2">
        <span class="text-xs">{{ expanded ? '▼' : '▶' }}</span>
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[3px]">{{ t('watch.title') }}</p>
        <span v-if="activeWatchedCount > 0" class="w-2 h-2 rounded-full bg-[var(--red)] animate-pulse"></span>
      </div>
      <span class="text-xs text-[var(--muted)]">{{ watchedIds.length }} {{ t('watch.watching') }}</span>
    </div>

    <div v-show="expanded" class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5">
      <p v-if="watchedIds.length === 0" class="text-xs text-[var(--muted)] mb-4">
        {{ t('watch.hint') }}
      </p>
      <div class="grid grid-cols-2 gap-2">
        <label v-for="chain in chains" :key="chain.id"
               class="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors"
               :class="isWatched(chain.id) ? 'bg-white/[0.04]' : 'hover:bg-white/[0.02]'">
          <input type="checkbox" :checked="isWatched(chain.id)" @change="toggle(chain.id)"
                 class="w-3.5 h-3.5 rounded accent-[var(--accent)]" />
          <span class="flex-1 text-xs" :class="chain.active ? 'text-white' : 'text-[var(--muted)]'">
            {{ tx(chain.name) }}
          </span>
          <span v-if="chain.active && isWatched(chain.id)" class="w-2 h-2 rounded-full bg-[var(--red)] animate-pulse"></span>
          <span v-else-if="chain.active" class="text-[9px] text-[var(--orange)]">{{ t('common.active') }}</span>
          <span class="text-[9px] font-mono" :style="{ color: chain.stress > 45 ? 'var(--red)' : chain.stress > 30 ? 'var(--orange)' : 'var(--muted)' }">
            {{ chain.stress.toFixed(0) }}
          </span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRiskStore } from '@/stores/risk'
import { useI18n } from '@/composables/useI18n'

const riskStore = useRiskStore()
const { t, tx } = useI18n()
const expanded = ref(false)
const watchedIds = ref<string[]>(JSON.parse(localStorage.getItem('gfcri_watched_chains') || '[]'))

const chains = computed(() => {
  const raw = riskStore.latest?.chain_details
  if (!raw) return []
  const list = Array.isArray(raw) ? raw : Object.values(raw)
  return list.sort((a: any, b: any) => b.stress - a.stress)
})

const activeWatchedCount = computed(() => {
  return chains.value.filter((c: any) => c.active && watchedIds.value.includes(c.id)).length
})

function isWatched(id: string) { return watchedIds.value.includes(id) }

function toggle(id: string) {
  if (isWatched(id)) {
    watchedIds.value = watchedIds.value.filter(x => x !== id)
  } else {
    watchedIds.value = [...watchedIds.value, id]
  }
  localStorage.setItem('gfcri_watched_chains', JSON.stringify(watchedIds.value))
}
</script>
