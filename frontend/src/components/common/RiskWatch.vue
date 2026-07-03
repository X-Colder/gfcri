<template>
  <div :class="compact ? '' : 'mb-8 fade-in'" v-if="chains.length">
    <template v-if="compact">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 lg:p-5 card-hover">
        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0">
            <p class="text-[11px] text-[var(--muted)] uppercase tracking-[3px]">{{ t('watch.context') }}</p>
            <div class="mt-1 flex items-center gap-2">
              <h3 class="text-sm font-medium text-white">{{ t('watch.title') }}</h3>
              <span v-if="activeWatchedCount > 0" class="h-2 w-2 rounded-full bg-[var(--red)] animate-pulse"></span>
            </div>
          </div>
          <button
            class="shrink-0 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--muted)] transition-colors hover:border-[var(--accent)] hover:text-white"
            type="button"
            @click="expanded = !expanded"
          >
            {{ expanded ? t('watch.done') : t('watch.manage') }}
          </button>
        </div>

        <div class="mt-4 grid grid-cols-2 gap-2">
          <div class="rounded-lg border border-[var(--border)] bg-white/[0.015] px-3 py-2">
            <p class="text-[10px] uppercase tracking-[2px] text-[var(--muted)]">{{ t('watch.selected') }}</p>
            <p class="mt-1 font-mono text-lg text-white">{{ watchItems.length }}</p>
          </div>
          <div class="rounded-lg border border-[var(--border)] bg-white/[0.015] px-3 py-2">
            <p class="text-[10px] uppercase tracking-[2px] text-[var(--muted)]">{{ t('watch.active') }}</p>
            <p class="mt-1 font-mono text-lg" :style="{ color: activeWatchedCount > 0 ? 'var(--red)' : 'var(--green)' }">
              {{ activeWatchedCount }}
            </p>
          </div>
        </div>

        <div class="mt-4 space-y-2">
          <div v-for="row in compactWatchRows" :key="row.key"
               class="flex items-center gap-3 rounded-lg border border-[var(--border)]/70 bg-white/[0.012] px-3 py-2">
            <span class="h-2 w-2 shrink-0 rounded-full"
                  :style="{ backgroundColor: row.color }"></span>
            <span class="min-w-0 flex-1 truncate text-xs" :class="row.active ? 'text-white' : 'text-[var(--muted)]'">
              {{ row.name }}
            </span>
            <span class="shrink-0 font-mono text-[10px]"
                  :style="{ color: row.color }">
              {{ row.score }}
            </span>
          </div>
          <p v-if="watchItems.length === 0" class="text-xs leading-relaxed text-[var(--muted)]">
            {{ t('watch.hint') }}
          </p>
        </div>

        <div v-show="expanded" class="mt-4 border-t border-[var(--border)] pt-4">
          <div class="grid gap-2 sm:grid-cols-2">
            <label v-for="chain in chains" :key="chain.id"
                   class="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors"
                   :class="isWatched(chain.id) ? 'bg-white/[0.04]' : 'hover:bg-white/[0.02]'">
              <input type="checkbox" :checked="isWatched(chain.id)" @change="toggle(chain.id)"
                     class="w-3.5 h-3.5 rounded accent-[var(--accent)]" />
              <span class="flex-1 truncate text-xs" :class="chain.active ? 'text-white' : 'text-[var(--muted)]'">
                {{ tx(chain.name) }}
              </span>
              <span v-if="chain.active && isWatched(chain.id)" class="w-2 h-2 rounded-full bg-[var(--red)] animate-pulse"></span>
              <span v-else-if="chain.active" class="text-[9px] text-[var(--orange)]">{{ t('common.active') }}</span>
              <span class="text-[9px] font-mono" :style="{ color: chain.stress > 45 ? 'var(--red)' : chain.stress > 30 ? 'var(--orange)' : 'var(--muted)' }">
                {{ Number(chain.stress || 0).toFixed(0) }}
              </span>
            </label>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="flex items-center justify-between mb-3 cursor-pointer" @click="expanded = !expanded">
        <div class="flex items-center gap-2">
          <span class="text-xs">{{ expanded ? '▼' : '▶' }}</span>
          <p class="text-[11px] text-[var(--muted)] uppercase tracking-[3px]">{{ t('watch.title') }}</p>
          <span v-if="activeWatchedCount > 0" class="w-2 h-2 rounded-full bg-[var(--red)] animate-pulse"></span>
        </div>
        <span class="text-xs text-[var(--muted)]">{{ watchItems.length }} {{ t('watch.watching') }}</span>
      </div>

      <div v-show="expanded" class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5">
        <p v-if="watchItems.length === 0" class="text-xs text-[var(--muted)] mb-4">
          {{ t('watch.hint') }}
        </p>
        <div class="grid gap-2 md:grid-cols-2">
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
              {{ Number(chain.stress || 0).toFixed(0) }}
            </span>
          </label>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRiskStore } from '@/stores/risk'
import { useI18n } from '@/composables/useI18n'
import { useRiskWatch } from '@/composables/useRiskWatch'

const riskStore = useRiskStore()
const { t, tx } = useI18n()
defineProps<{ compact?: boolean }>()
const expanded = ref(false)
const riskWatch = useRiskWatch()
const watchedIds = riskWatch.watchedChainIds
const watchItems = riskWatch.items

const chains = computed(() => {
  const raw = riskStore.latest?.chain_details
  if (!raw) return []
  const list = Array.isArray(raw) ? raw : Object.values(raw)
  return list.sort((a: any, b: any) => b.stress - a.stress)
})

const activeWatchedCount = computed(() => {
  const activeChains = chains.value.filter((c: any) => c.active && watchedIds.value.includes(c.id)).length
  const activeIndicators = watchedIndicators.value.filter(item => item.active).length
  return activeChains + activeIndicators
})

const watchedChains = computed(() => {
  return chains.value.filter((c: any) => watchedIds.value.includes(c.id))
})

const watchedIndicators = computed(() => {
  const nc = riskStore.latest?.node_contributions || {}
  return watchItems.value
    .filter(item => item.type === 'indicator')
    .map(item => {
      const info: any = (nc as any)[item.id] || {}
      const abs = info.abs_score === null || info.abs_score === undefined ? null : Number(info.abs_score)
      const anomaly = Number(info.anomaly_score || 0)
      const pressure = Math.max(abs || 0, anomaly) * 100
      return {
        id: item.id,
        name: tx(info.display_name || item.label || item.id),
        pressure,
        active: pressure >= 40,
      }
    })
})

const compactChains = computed(() => {
  const candidates = watchedChains.value.length
    ? watchedChains.value
    : chains.value.filter((c: any) => c.active)
  return (candidates.length ? candidates : chains.value).slice(0, 3)
})

const compactWatchRows = computed(() => {
  const chainRows = watchedChains.value.map((chain: any) => ({
    key: `chain:${chain.id}`,
    name: tx(chain.name),
    score: Number(chain.stress || 0).toFixed(0),
    color: chain.active ? 'var(--red)' : chain.stress > 35 ? 'var(--orange)' : 'var(--muted)',
    active: !!chain.active,
  }))
  const indicatorRows = watchedIndicators.value.map(item => ({
    key: `indicator:${item.id}`,
    name: item.name,
    score: item.pressure.toFixed(0),
    color: item.pressure >= 70 ? 'var(--red)' : item.pressure >= 40 ? 'var(--orange)' : 'var(--muted)',
    active: item.active,
  }))
  const watchedRows = [...chainRows, ...indicatorRows]
  if (watchedRows.length) return watchedRows.slice(0, 4)
  return compactChains.value.map((chain: any) => ({
    key: `chain:${chain.id}`,
    name: tx(chain.name),
    score: Number(chain.stress || 0).toFixed(0),
    color: chain.active ? 'var(--red)' : chain.stress > 35 ? 'var(--orange)' : 'var(--muted)',
    active: !!chain.active,
  }))
})

function isWatched(id: string) { return watchedIds.value.includes(id) }

function toggle(id: string) {
  const chain = chains.value.find((c: any) => c.id === id)
  riskWatch.toggle({
    type: 'chain',
    id,
    label: chain ? tx(chain.name) : id,
    reason: chain?.active ? t('common.active') : t('common.dormant'),
  })
}
</script>
