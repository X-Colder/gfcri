<template>
  <div>
    <!-- Header with run button -->
    <div class="flex items-center justify-between mb-8 fade-in">
      <div>
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">{{ t('forward.kicker') }}</p>
        <h2 class="text-lg font-light text-white">{{ t('forward.title') }}</h2>
      </div>
      <button @click="loadAll" :disabled="loading"
              class="px-4 py-2 rounded-lg bg-[var(--accent)]/15 text-[var(--accent)] text-sm font-medium hover:bg-[var(--accent)]/25 transition-colors disabled:opacity-50">
        {{ loading ? t('common.loading') : t('common.refresh') }}
      </button>
    </div>

    <Paywall :blurred="!isPro" :title="t('forward.unlockTitle')" :description="t('forward.unlockDesc')">

      <!-- Section 1: Crisis Distance — How far from crisis? -->
      <div class="mb-12 fade-in">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">{{ t('forward.thresholdKicker') }}</p>
        <div class="mb-6 flex items-center justify-between gap-4">
          <h3 class="text-lg font-light text-white">{{ t('forward.crisis') }}</h3>
          <span v-if="crisisLoading" class="text-[10px] text-[var(--muted)] font-mono">{{ t('common.loading') }}</span>
        </div>
        <p class="text-xs text-[var(--muted)] mb-5 max-w-2xl">{{ t('forward.crisisHelp') }}</p>

        <div v-if="crisisLoading && !crisisData" class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
          <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div v-for="i in 4" :key="i" class="h-28 rounded-lg bg-white/[0.025] animate-pulse"></div>
          </div>
        </div>

        <!-- Overall + 3 tiers -->
        <div v-else-if="crisisData" class="grid gap-4 mb-6 md:grid-cols-2 xl:grid-cols-4">
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 text-center card-hover">
            <p class="text-[10px] text-[var(--muted)] uppercase tracking-wider mb-2">{{ t('forward.overall') }}</p>
            <p class="text-4xl font-extralight font-mono" :style="{ color: distColor(crisisData.overall_distance) }">
              {{ crisisData.overall_distance.toFixed(0) }}%
            </p>
            <p class="text-xs mt-2" :style="{ color: distColor(crisisData.overall_distance) }">{{ probLabel(crisisData.overall_probability) }}</p>
          </div>
          <div v-for="(tier, i) in [
            { key: 'tier1_distance', label: t('forward.global'), desc: 'VIX · Credit · USD' },
            { key: 'tier2_distance', label: t('forward.usCore'), desc: 'SPX · Bonds · Oil · Gold' },
            { key: 'tier3_distance', label: t('forward.regional'), desc: 'KRW · HSI · EUR' },
          ]" :key="i"
               class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 text-center card-hover">
            <p class="text-[10px] text-[var(--muted)] uppercase tracking-wider mb-2">{{ tier.label }}</p>
            <p class="text-3xl font-extralight font-mono" :style="{ color: distColor(crisisData[tier.key]) }">
              {{ crisisData[tier.key].toFixed(0) }}%
            </p>
            <p class="text-[10px] text-[var(--muted)] mt-2">{{ tier.desc }}</p>
          </div>
        </div>

        <!-- Distance bars -->
        <div v-if="crisisData" class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
          <div v-for="tierNum in [1,2,3]" :key="tierNum" class="mb-5 last:mb-0">
            <p class="text-[10px] text-[var(--muted)] uppercase tracking-wider mb-3">
              {{ t('common.level') }} {{ tierNum }} — {{ tierNum === 1 ? t('forward.global') : tierNum === 2 ? t('forward.usCore') : t('forward.regional') }}
            </p>
            <div class="space-y-3">
              <div v-for="d in crisisData.distances.filter((x: any) => x.tier === tierNum)" :key="d.node_id">
                <div class="flex items-center justify-between text-xs mb-1">
                  <div class="flex items-center gap-2">
                    <span class="text-white">{{ tx(d.name) }}</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded"
                          :class="d.status === 'crisis' ? 'bg-[var(--red)]/10 text-[var(--red)]' : d.status === 'warning' ? 'bg-[var(--yellow)]/10 text-[var(--yellow)]' : 'bg-[var(--green)]/10 text-[var(--green)]'">
                      {{ d.status === 'crisis' ? t('forward.danger') : d.status === 'warning' ? t('forward.warn') : t('forward.safe') }}
                    </span>
                  </div>
                  <span class="font-mono text-[var(--muted)] text-[11px]">{{ d.current_value.toFixed(1) }}</span>
                </div>
                <div class="relative h-2.5 bg-white/[0.03] rounded-full overflow-hidden">
                  <div class="absolute top-0 h-full rounded-full transition-all duration-700"
                       :style="{ width: Math.min(d.distance_pct, 100) + '%', backgroundColor: distColor(d.distance_pct) }"></div>
                </div>
                <p class="text-[9px] text-[var(--muted)]/50 mt-1">{{ t('forward.worstHist') }}: {{ tx(d.worst_event) }} ({{ d.worst_value }})</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Section 2: Stress Test Scenarios — What if? -->
      <div class="mb-12 fade-in fade-in-delay-1">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">{{ t('forward.stressKicker') }}</p>
        <div class="mb-6 flex items-center justify-between gap-4">
          <h3 class="text-lg font-light text-white">{{ t('forward.stress') }}</h3>
          <span v-if="stressLoading" class="text-[10px] text-[var(--muted)] font-mono">{{ t('common.loading') }}</span>
        </div>

        <div v-if="stressLoading && !stressResults.length" class="grid gap-4 lg:grid-cols-2">
          <div v-for="i in 4" :key="i" class="h-32 rounded-xl bg-[var(--card)] border border-[var(--border)] animate-pulse"></div>
        </div>

        <div v-else-if="stressResults.length" class="grid gap-4 lg:grid-cols-2">
          <div v-for="sr in sortedStress" :key="sr.scenario_name"
               class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 card-hover"
               :class="sr.gfcri_delta > 10 ? 'border-l-[3px] border-l-[var(--red)]' : sr.gfcri_delta > 5 ? 'border-l-[3px] border-l-[var(--orange)]' : ''">
            <div class="flex justify-between items-start mb-3">
              <h4 class="text-sm text-white font-medium">{{ tx(sr.scenario_name) }}</h4>
              <span class="text-xs font-mono text-[var(--red)]">+{{ sr.gfcri_delta.toFixed(0) }}</span>
            </div>
            <p class="text-xs text-[var(--muted)] mb-3">{{ tx(sr.scenario_description) }}</p>
            <div class="flex items-center gap-3">
              <span class="text-[var(--muted)] font-mono text-sm">{{ sr.baseline_gfcri.toFixed(0) }}</span>
              <span class="text-[var(--muted)]">→</span>
              <span class="font-mono text-lg" :style="{ color: sr.stressed_gfcri >= 60 ? 'var(--red)' : sr.stressed_gfcri >= 45 ? 'var(--orange)' : 'var(--yellow)' }">
                {{ sr.stressed_gfcri.toFixed(0) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Policy buffers -->
      <div class="mb-12 fade-in fade-in-delay-3" v-if="crisisData?.policies?.length">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">{{ t('forward.policyKicker') }}</p>
        <h3 class="text-lg font-light text-white mb-6">{{ t('forward.policy') }}</h3>

        <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div v-for="p in crisisData.policies" :key="p.name"
               class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 card-hover">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs text-white font-medium">{{ tx(p.name) }}</span>
              <span class="text-[9px] px-1.5 py-0.5 rounded"
                    :class="p.status === 'buffer' ? 'bg-[var(--green)]/10 text-[var(--green)]' : p.status === 'warning' ? 'bg-[var(--red)]/10 text-[var(--red)]' : 'bg-[var(--yellow)]/10 text-[var(--yellow)]'">
                {{ p.status === 'buffer' ? t('forward.hasBuffer') : p.status === 'warning' ? t('forward.warning') : t('forward.neutral') }}
              </span>
            </div>
            <p class="text-[11px] text-[var(--muted)] leading-relaxed">{{ tx(p.detail) }}</p>
          </div>
        </div>
      </div>

      </Paywall>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { COLORS } from '@/composables/useTheme'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'
import Paywall from '@/components/common/Paywall.vue'
import client from '@/api/client'

const { isPro } = useAuth()
const { t, tx } = useI18n()
const crisisData = ref<any>(null)
const stressResults = ref<any[]>([])
const crisisLoading = ref(false)
const stressLoading = ref(false)
const loading = computed(() => crisisLoading.value || stressLoading.value)

function distColor(d: number): string {
  if (d >= 70) return COLORS.red
  if (d >= 40) return COLORS.orange
  if (d >= 20) return COLORS.yellow
  return COLORS.green
}

function probLabel(p: string): string {
  return { low: t('forward.lowRisk'), medium: t('forward.medRisk'), high: t('forward.highRisk'), critical: t('forward.critRisk') }[p] || p
}

const sortedStress = computed(() =>
  [...stressResults.value].sort((a, b) => b.gfcri_delta - a.gfcri_delta)
)

async function loadAll() {
  await Promise.allSettled([loadCrisis(), loadStress()])
}

async function loadCrisis() {
  crisisLoading.value = true
  try {
    const { data } = await client.get('/crisis-distance')
    crisisData.value = data
  } catch (e) {
    console.error('Crisis distance load failed', e)
  } finally {
    crisisLoading.value = false
  }
}

async function loadStress() {
  stressLoading.value = true
  try {
    const { data } = await client.get('/stress-test/run-all')
    stressResults.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error('Stress test load failed', e)
  } finally {
    stressLoading.value = false
  }
}

onMounted(() => loadAll())

</script>
