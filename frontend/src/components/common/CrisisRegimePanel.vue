<template>
  <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 lg:p-5 card-hover">
    <div v-if="loading" class="py-8 text-center text-xs text-[var(--muted)]">{{ t('common.loading') }}</div>
    <div v-else-if="assessment">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div class="min-w-0">
          <p class="text-[11px] text-[var(--muted)] uppercase tracking-[3px]">{{ t('regime.kicker') }}</p>
          <div class="mt-1 flex flex-wrap items-center gap-3">
            <h3 class="text-sm font-medium text-white">{{ t('regime.title') }}</h3>
            <span class="rounded-full border px-2 py-0.5 text-[10px] font-mono"
                  :style="{ color: damageColor, borderColor: damageColor, backgroundColor: damageColor + '18' }">
              D{{ damage.level.level }} · {{ levelLabel(damage.level) }}
            </span>
          </div>
          <p class="terminal-copy mt-2">{{ assessment.interpretation }}</p>
        </div>
        <div class="grid grid-cols-3 gap-2 sm:min-w-[390px]">
          <div class="terminal-metric">
            <span>{{ t('regime.damage') }}</span>
            <strong :style="{ color: damageColor }">{{ Number(damage.score || 0).toFixed(1) }}</strong>
          </div>
          <div class="terminal-metric">
            <span>{{ t('regime.pressure') }}</span>
            <strong :style="{ color: pressureColor }">{{ Number(pressure.score || 0).toFixed(1) }}</strong>
          </div>
          <div class="terminal-metric">
            <span>{{ t('regime.hidden') }}</span>
            <strong :style="{ color: hiddenColor }">{{ Number(hidden.score || 0).toFixed(0) }}</strong>
          </div>
        </div>
      </div>

      <div class="mt-4 h-2 overflow-hidden rounded-full bg-white/[0.05]">
        <div class="h-full rounded-full transition-all" :style="{ width: damageWidth, backgroundColor: damageColor }"></div>
      </div>
      <div class="mt-2 grid grid-cols-6 gap-1 text-[9px] text-[var(--muted)]">
        <span v-for="level in damageLevels" :key="level.id" class="truncate">{{ levelLabel(level) }}</span>
      </div>

      <div class="mt-4 grid gap-3 lg:grid-cols-3">
        <div class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-3">
          <p class="text-[10px] uppercase tracking-[2px] text-[var(--muted)]">{{ t('regime.realizedDamage') }}</p>
          <p class="mt-1 text-xs text-white">{{ levelLabel(damage.level) }}</p>
          <p class="mt-1 text-[11px] leading-relaxed text-[var(--muted)]">{{ damage.level?.economy_reference }}</p>
        </div>
        <div class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-3">
          <p class="text-[10px] uppercase tracking-[2px] text-[var(--muted)]">{{ t('regime.forwardPressure') }}</p>
          <p class="mt-1 text-xs text-white">{{ levelLabel(pressure.level) }}</p>
          <p class="mt-1 text-[11px] leading-relaxed text-[var(--muted)]">{{ pressure.level?.description }}</p>
        </div>
        <div class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-3">
          <p class="text-[10px] uppercase tracking-[2px] text-[var(--muted)]">{{ t('regime.hiddenRisk') }}</p>
          <p class="mt-1 text-xs text-white">{{ hiddenLabel }}</p>
          <p class="mt-1 text-[11px] leading-relaxed text-[var(--muted)]">{{ t('regime.hiddenNote') }}</p>
        </div>
      </div>

      <div class="mt-5 grid gap-4" :class="compact ? 'xl:grid-cols-2' : 'xl:grid-cols-[minmax(0,1.05fr)_minmax(340px,0.95fr)]'">
        <div class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
          <div class="mb-3 flex items-center justify-between">
            <p class="text-xs font-medium text-white">{{ t('regime.factorContribution') }}</p>
            <span class="text-[10px] text-[var(--muted)]">{{ t('regime.weighted') }}</span>
          </div>
          <div class="space-y-3">
            <div v-for="factor in visibleFactors" :key="factor.id" class="grid grid-cols-[minmax(0,130px)_1fr_auto] items-center gap-2">
              <span class="truncate text-xs text-[var(--muted)]">{{ factorName(factor) }}</span>
              <div class="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                <div class="h-full rounded-full" :style="{ width: Math.min(Number(factor.share || 0), 100) + '%', backgroundColor: factorColor(Number(factor.score || 0)) }"></div>
              </div>
              <span class="w-12 text-right font-mono text-[10px] text-white">{{ Number(factor.share || 0).toFixed(0) }}%</span>
            </div>
          </div>
        </div>

        <div class="rounded-lg border border-[var(--border)] bg-white/[0.012] overflow-hidden">
          <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
            <p class="text-xs font-medium text-white">{{ t('regime.closest') }}</p>
            <span class="text-[10px] text-[var(--muted)]">{{ t('regime.similarity') }}</span>
          </div>
          <div class="divide-y divide-[var(--border)]/50">
            <div v-for="match in visibleMatches" :key="match.id" class="px-4 py-3">
              <div class="flex items-center justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-xs text-white">{{ matchName(match) }}</p>
                  <p class="mt-1 text-[10px] text-[var(--muted)]">{{ match.peak_period }}</p>
                </div>
                <span class="font-mono text-xs" :style="{ color: factorColor(Number(match.similarity || 0)) }">{{ Number(match.similarity || 0).toFixed(0) }}%</span>
              </div>
              <p v-if="!compact" class="mt-2 text-[11px] leading-relaxed text-[var(--muted)]">{{ match.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!compact" class="mt-4 rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
        <div class="mb-3 flex items-center justify-between">
          <p class="text-xs font-medium text-white">{{ t('regime.damageEvidence') }}</p>
          <span class="text-[10px] text-[var(--muted)]">{{ t('regime.realizedDamage') }}</span>
        </div>
        <div class="grid gap-3 lg:grid-cols-2">
          <div v-for="item in damageEvidence" :key="item.id" class="grid grid-cols-[minmax(0,150px)_1fr_auto] items-center gap-2 rounded-lg border border-[var(--border)] p-3">
            <span class="truncate text-xs text-[var(--muted)]">{{ damageEvidenceName(item) }}</span>
            <div class="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
              <div class="h-full rounded-full" :style="{ width: Math.min(Number(item.score || 0), 100) + '%', backgroundColor: factorColor(Number(item.score || 0)) }"></div>
            </div>
            <span class="w-10 text-right font-mono text-[10px] text-white">{{ Number(item.score || 0).toFixed(0) }}</span>
          </div>
        </div>
      </div>

      <div v-if="!compact" class="mt-4 rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
        <div class="mb-3 flex items-center justify-between">
          <p class="text-xs font-medium text-white">{{ t('regime.currentEvidence') }}</p>
          <span class="text-[10px] text-[var(--muted)]">{{ t('regime.forwardPressure') }}</span>
        </div>
        <div class="grid gap-3 lg:grid-cols-3">
          <div v-for="item in currentEvidence" :key="item.id" class="rounded-lg border border-[var(--border)] p-3">
            <p class="text-[10px] uppercase tracking-[2px] text-[var(--muted)]">{{ item.label }}</p>
            <p class="mt-1 font-mono text-sm text-white">{{ item.value }}</p>
            <p class="mt-1 text-[11px] leading-relaxed text-[var(--muted)]">{{ item.detail }}</p>
          </div>
        </div>
        <div v-if="topIndicators.length" class="mt-4 overflow-x-auto rounded-lg border border-[var(--border)]">
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-[var(--border)] text-[var(--muted)]">
                <th class="px-3 py-2 text-left font-medium">{{ t('analysis.indicator') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ t('analysis.current') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ t('analysis.zscore') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ t('analysis.absScore') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="node in topIndicators" :key="node.id" class="border-b border-[var(--border)]/50 last:border-b-0">
                <td class="px-3 py-2 text-white">{{ node.name }}</td>
                <td class="px-3 py-2 text-right font-mono text-[var(--muted)]">{{ node.current }}</td>
                <td class="px-3 py-2 text-right font-mono" :style="{ color: Math.abs(node.zscore) >= 2 ? 'var(--red)' : 'var(--muted)' }">{{ node.zscore.toFixed(2) }}</td>
                <td class="px-3 py-2 text-right font-mono">{{ node.abs }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="!compact" class="mt-4 rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
        <p class="mb-3 text-xs font-medium text-white">{{ t('regime.reference') }}</p>
        <div class="grid gap-3 lg:grid-cols-2">
          <div v-for="level in damageLevels" :key="level.id" class="rounded-lg border border-[var(--border)] p-3">
            <p class="text-xs text-white">L{{ level.level }} · {{ levelLabel(level) }}</p>
            <p class="mt-1 text-[11px] leading-relaxed text-[var(--muted)]">{{ level.market_reference }}</p>
            <p class="mt-1 text-[11px] leading-relaxed text-[var(--muted)]">{{ level.economy_reference }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import client from '@/api/client'
import { COLORS } from '@/composables/useTheme'
import { useI18n } from '@/composables/useI18n'
import { useRiskStore } from '@/stores/risk'

defineProps<{ compact?: boolean }>()

const { t, lang } = useI18n()
const riskStore = useRiskStore()
const assessment = ref<any>(null)
const loading = ref(false)

onMounted(loadAssessment)

async function loadAssessment() {
  loading.value = true
  try {
    const { data } = await client.get('/regime-assessment/latest')
    assessment.value = data
    if (!riskStore.latest) await riskStore.loadLatest()
  } catch (e) {
    assessment.value = null
  } finally {
    loading.value = false
  }
}

const visibleFactors = computed(() => (assessment.value?.factors || []).slice(0, 8))
const visibleMatches = computed(() => (assessment.value?.matches || []).slice(0, 3))
const damage = computed(() => assessment.value?.realized_damage || { score: 0, level: assessment.value?.level || {} })
const pressure = computed(() => assessment.value?.forward_pressure || { score: assessment.value?.score || 0, level: {} })
const hidden = computed(() => assessment.value?.hidden_risk || { score: 0, label: 'Low Hidden Risk', label_zh: '低隐藏风险' })
const damageLevels = computed(() => assessment.value?.damage_levels || assessment.value?.levels || [])
const damageEvidence = computed(() => assessment.value?.realized_damage?.evidence || [])
const damageColor = computed(() => factorColor(Number(damage.value?.score || 0)))
const pressureColor = computed(() => factorColor(Number(pressure.value?.score || 0)))
const hiddenColor = computed(() => factorColor(Number(hidden.value?.score || 0)))
const damageWidth = computed(() => `${Math.min(Number(damage.value?.score || 0), 100)}%`)
const hiddenLabel = computed(() => lang.value === 'zh' ? hidden.value?.label_zh || hidden.value?.label : hidden.value?.label)

const currentEvidence = computed(() => {
  const latest = riskStore.latest
  const sub = latest?.sub_index_details || {}
  const trade = latest?.trade_spillover || sub.SI_TRADE_SPILLOVER?.trade_spillover || {}
  return [
    {
      id: 'gfcri',
      label: t('regime.pressure'),
      value: latest ? Number(latest.gfcri_value || 0).toFixed(1) : '-',
      detail: pressure.value?.level?.description || '',
    },
    {
      id: 'coherence',
      label: t('dash.coherence'),
      value: `${Number(latest?.coherence_multiplier || 1).toFixed(2)}x`,
      detail: `${activeChainCount.value} ${t('analysis.chainActive')} / ${t('analysis.chainTitle')}`,
    },
    {
      id: 'trade',
      label: t('trade.title'),
      value: `${Number(trade?.score || 0).toFixed(1)} / +${Number(latest?.trade_spillover_boost || 0).toFixed(1)}`,
      detail: topTradeLink.value,
    },
    {
      id: 'hidden',
      label: t('regime.hiddenRisk'),
      value: `${Number(hidden.value?.score || 0).toFixed(0)}`,
      detail: `${t('analysis.undercurrentBoost')} +${Number(latest?.undercurrent_boost || 0).toFixed(1)}`,
    },
    {
      id: 'damage',
      label: t('regime.realizedDamage'),
      value: `${Number(damage.value?.score || 0).toFixed(1)}`,
      detail: topDamageEvidence.value,
    },
    {
      id: 'match',
      label: t('regime.closest'),
      value: visibleMatches.value[0] ? `${Number(visibleMatches.value[0].similarity || 0).toFixed(0)}%` : '-',
      detail: visibleMatches.value[0] ? matchName(visibleMatches.value[0]) : '-',
    },
  ]
})

const activeChainCount = computed(() => {
  const raw = riskStore.latest?.chain_details || []
  const list = Array.isArray(raw) ? raw : Object.values(raw)
  return list.filter((c: any) => c.active).length
})

const topTradeLink = computed(() => {
  const latest = riskStore.latest
  const sub = latest?.sub_index_details || {}
  const trade = latest?.trade_spillover || sub.SI_TRADE_SPILLOVER?.trade_spillover || {}
  const link = Array.isArray(trade?.top_links) ? trade.top_links[0] : null
  if (!link) return t('trade.empty')
  return `${link.source_name || link.source} -> ${link.target_name || link.target}: ${Number(link.spillover || 0).toFixed(1)}`
})

const topDamageEvidence = computed(() => {
  const top = damageEvidence.value[0]
  if (!top) return '-'
  return `${damageEvidenceName(top)} ${Number(top.score || 0).toFixed(0)}`
})

const topIndicators = computed(() => {
  const nc = riskStore.latest?.node_contributions || {}
  return Object.entries(nc)
    .map(([id, info]: [string, any]) => {
      const zscore = Number(info.zscore || 0)
      const anomaly = Number(info.anomaly_score || 0)
      const abs = info.abs_score === null || info.abs_score === undefined ? null : Number(info.abs_score)
      return {
        id,
        name: String(info.display_name || id),
        current: formatValue(info.current_value),
        zscore,
        abs: abs === null ? '-' : (abs * 100).toFixed(0),
        sortScore: Math.max(Math.abs(zscore) / 4, anomaly, abs || 0),
      }
    })
    .sort((a, b) => b.sortScore - a.sortScore)
    .slice(0, 6)
})

function factorColor(value: number): string {
  if (value >= 75) return COLORS.red
  if (value >= 50) return COLORS.orange
  if (value >= 25) return COLORS.yellow
  return COLORS.green
}

function levelLabel(level: any): string {
  return lang.value === 'zh' ? level.label_zh || level.label : level.label
}

function factorName(factor: any): string {
  return lang.value === 'zh' ? factor.name_zh || factor.name : factor.name
}

function damageEvidenceName(item: any): string {
  return lang.value === 'zh' ? item.name_zh || item.name : item.name
}

function matchName(match: any): string {
  return lang.value === 'zh' ? match.name_zh || match.name : match.name
}

function formatValue(value: any): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  const n = Number(value)
  if (Math.abs(n) >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 0 })
  if (Math.abs(n) >= 10) return n.toFixed(1)
  return n.toFixed(2)
}
</script>
