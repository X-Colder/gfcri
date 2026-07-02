<template>
  <div class="space-y-6">
    <h2 class="text-xl font-bold">{{ t('crisis.title') }}</h2>

    <LoadingSpinner v-if="loading" />

    <template v-else-if="data">
      <!-- Overall -->
      <div class="bg-card border border-border rounded-xl p-6 text-center">
        <p class="text-xs text-muted mb-2">{{ t('forward.crisis') }}</p>
        <p class="text-5xl font-bold font-mono" :style="{ color: probColor(data.overall_probability) }">{{ data.overall_distance.toFixed(0) }}%</p>
        <p class="text-sm mt-2" :style="{ color: probColor(data.overall_probability) }">{{ probLabel(data.overall_probability) }}</p>
        <div class="flex justify-center gap-1 mt-3">
          <span v-for="lvl in ['low','medium','high','critical']" :key="lvl" class="px-3 py-1 rounded-full text-[10px]" :style="{ backgroundColor: data.overall_probability === lvl ? probColor(lvl) + '20' : '#1a1d24', color: data.overall_probability === lvl ? probColor(lvl) : '#8b949e', border: data.overall_probability === lvl ? '1px solid ' + probColor(lvl) : '1px solid transparent' }">
            {{ probLabel(lvl) }}
          </span>
        </div>
      </div>

      <!-- Distance Gauges -->
      <div class="bg-card border border-border rounded-xl p-5">
        <p class="text-sm font-medium mb-4">{{ t('crisis.indicatorDistance') }}</p>
        <div class="space-y-3">
          <div v-for="d in data.distances" :key="d.node_id">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs">{{ tx(d.name) }}</span>
              <div class="flex items-center gap-3 text-xs font-mono">
                <span class="text-muted">{{ t('common.current') }} {{ d.current_value }}</span>
                <span class="text-muted">|</span>
                <span :style="{ color: distColor(d.distance_pct) }">{{ t('common.crisis') }} {{ d.crisis_threshold }}</span>
              </div>
            </div>
            <!-- Distance bar -->
            <div class="relative h-5 bg-bg rounded-full overflow-hidden">
              <!-- Crisis zone markers -->
              <div class="absolute inset-0 flex">
                <div class="h-full" style="width:30%;background:rgba(46,160,67,0.1)"></div>
                <div class="h-full" style="width:20%;background:rgba(210,153,34,0.1)"></div>
                <div class="h-full" style="width:20%;background:rgba(219,109,40,0.1)"></div>
                <div class="h-full" style="width:30%;background:rgba(248,81,73,0.1)"></div>
              </div>
              <!-- Current position -->
              <div class="absolute top-0 h-full rounded-full transition-all" :style="{ width: Math.min(d.distance_pct, 100) + '%', backgroundColor: distColor(d.distance_pct) }"></div>
              <!-- Labels -->
              <div class="absolute inset-0 flex items-center justify-between px-2">
                <span class="text-[9px] text-muted z-10">{{ t('common.safe') }}</span>
                <span class="text-[9px] text-muted z-10">{{ t('common.crisis') }}</span>
              </div>
            </div>
            <!-- Historical crisis reference -->
            <p class="text-[10px] text-muted mt-0.5">{{ t('forward.worstHist') }}: {{ tx(d.worst_crisis_event) }} ({{ d.worst_crisis_value }})</p>
          </div>
        </div>
      </div>

      <!-- Policy Buffers -->
      <div class="bg-card border border-border rounded-xl p-5">
        <p class="text-sm font-medium mb-4">{{ t('crisis.policy') }}</p>
        <div class="grid grid-cols-2 gap-3">
          <div v-for="p in data.policies" :key="p.name" class="bg-bg rounded-lg p-3">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-medium">{{ tx(p.name) }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded" :class="p.status === 'buffer' ? 'bg-alert-green/10 text-alert-green' : p.status === 'warning' ? 'bg-alert-red/10 text-alert-red' : 'bg-alert-yellow/10 text-alert-yellow'">
                {{ p.status === 'buffer' ? t('forward.hasBuffer') : p.status === 'warning' ? t('forward.warning') : t('forward.neutral') }}
              </span>
            </div>
            <div class="h-1.5 bg-border rounded-full overflow-hidden my-1.5">
              <div class="h-full rounded-full" :style="{ width: p.score + '%', backgroundColor: p.status === 'buffer' ? '#2ea043' : p.status === 'warning' ? '#f85149' : '#d29922' }"></div>
            </div>
            <p class="text-[10px] text-muted">{{ tx(p.detail) }}</p>
          </div>
        </div>
      </div>

      <!-- Summary -->
      <div class="grid grid-cols-2 gap-3">
        <div class="bg-card border border-border rounded-xl p-4">
          <p class="text-xs text-muted mb-2">{{ t('crisis.closest') }}</p>
          <div v-for="c in data.closest_indicators" :key="c.name" class="flex items-center justify-between py-1">
            <span class="text-xs">{{ tx(c.name) }}</span>
            <span class="text-xs font-mono font-bold" :style="{ color: distColor(c.distance) }">{{ c.distance.toFixed(0) }}%</span>
          </div>
        </div>
        <div class="bg-card border border-border rounded-xl p-4">
          <p class="text-xs text-muted mb-2">{{ t('crisis.farthest') }}</p>
          <div v-for="f in data.farthest_indicators" :key="f.name" class="flex items-center justify-between py-1">
            <span class="text-xs">{{ tx(f.name) }}</span>
            <span class="text-xs font-mono font-bold text-alert-green">{{ f.distance.toFixed(0) }}%</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import client from '@/api/client'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useI18n } from '@/composables/useI18n'

const data = ref<any>(null)
const loading = ref(false)
const { t, tx } = useI18n()

onMounted(async () => {
  loading.value = true
  try { data.value = (await client.get('/crisis-distance')).data } catch (e) { console.error(e) }
  finally { loading.value = false }
})

function probColor(p: string): string {
  return { low: '#2ea043', medium: '#d29922', high: '#db6d28', critical: '#f85149' }[p] || '#8b949e'
}
function probLabel(p: string): string {
  return { low: t('forward.lowRisk'), medium: t('forward.medRisk'), high: t('forward.highRisk'), critical: t('forward.critRisk') }[p] || p
}
function distColor(d: number): string {
  if (d >= 70) return '#f85149'
  if (d >= 50) return '#db6d28'
  if (d >= 30) return '#d29922'
  return '#2ea043'
}
</script>
