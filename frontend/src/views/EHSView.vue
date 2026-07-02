<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold">{{ t('ehs.title') }}</h2>
      <button @click="loadScores" :disabled="loading" class="px-4 py-2 rounded-lg bg-accent/15 text-accent text-sm font-medium hover:bg-accent/20 transition-colors disabled:opacity-50">
        {{ loading ? t('inference.running') : t('common.refresh') }}
      </button>
    </div>

    <LoadingSpinner v-if="loading" />

    <template v-else-if="scores.length">
      <!-- Summary Cards -->
      <div class="grid grid-cols-3 gap-4">
        <MetricCard :label="t('ehs.economies')" :value="scores.length" />
        <MetricCard :label="t('ehs.avg')" :value="avgScore.toFixed(1)" :color="scoreColor(avgScore)" />
        <MetricCard :label="t('ehs.recession')" :value="recessionCount" :color="recessionCount > 0 ? '#f85149' : '#2ea043'" />
      </div>

      <!-- Ranking Table -->
      <div class="bg-card border border-border rounded-xl p-5">
        <h3 class="text-sm font-medium text-muted mb-4">{{ t('ehs.ranking') }}</h3>
        <div class="space-y-2">
          <div
            v-for="(s, i) in scores"
            :key="s.economy_code"
            class="flex items-center gap-4 p-3 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
            @click="selectedEconomy = s"
          >
            <span class="text-sm text-muted w-6">{{ i + 1 }}</span>
            <div class="w-10 h-10 rounded-lg flex items-center justify-center text-lg" :style="{ backgroundColor: scoreColor(s.ehs_score) + '1a' }">
              {{ flagEmoji(s.economy_code) }}
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium">{{ tx(s.economy_name) }}</span>
                <span class="text-[10px] px-2 py-0.5 rounded-full" :style="{ color: cycleColor(s.cycle_phase), backgroundColor: cycleColor(s.cycle_phase) + '1a' }">
                  {{ tx(s.cycle_label) }}
                </span>
              </div>
              <div class="flex items-center gap-2 mt-1">
                <div class="flex-1 h-2 bg-bg rounded-full overflow-hidden max-w-[200px]">
                  <div class="h-full rounded-full transition-all" :style="{ width: s.ehs_score + '%', backgroundColor: scoreColor(s.ehs_score) }"></div>
                </div>
                <span class="text-sm font-mono font-bold" :style="{ color: scoreColor(s.ehs_score) }">{{ s.ehs_score.toFixed(1) }}</span>
              </div>
            </div>
            <!-- Dimension mini bars -->
            <div class="hidden lg:flex gap-1">
              <div v-for="dim in ['growth_score', 'labor_score', 'price_score', 'external_score', 'financial_score']" :key="dim" class="w-1.5 h-8 bg-bg rounded-full overflow-hidden flex flex-col-reverse">
                <div class="rounded-full transition-all" :style="{ height: s[dim] + '%', backgroundColor: scoreColor(s[dim]) }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Economy Detail Modal -->
      <div v-if="selectedEconomy" class="bg-card border border-border rounded-xl p-5">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <span class="text-2xl">{{ flagEmoji(selectedEconomy.economy_code) }}</span>
            <div>
              <h3 class="font-medium">{{ tx(selectedEconomy.economy_name) }}</h3>
              <span class="text-xs text-muted">{{ selectedEconomy.economy_code }}</span>
            </div>
          </div>
          <button @click="selectedEconomy = null" class="text-muted hover:text-white">✕</button>
        </div>

        <!-- Dimension Scores -->
        <div class="grid grid-cols-5 gap-3 mb-4">
          <div v-for="(label, dim) in dimLabels" :key="dim" class="text-center">
            <div class="text-lg font-bold font-mono" :style="{ color: scoreColor(selectedEconomy[dim]) }">{{ selectedEconomy[dim]?.toFixed(0) ?? '-' }}</div>
            <div class="text-[10px] text-muted mt-0.5">{{ label }}</div>
          </div>
        </div>

        <!-- Indicator Details -->
        <div v-if="selectedEconomy.indicator_details" class="border-t border-border pt-4">
          <h4 class="text-xs text-muted mb-3">{{ t('ehs.details') }}</h4>
          <div class="grid grid-cols-2 gap-2">
            <div v-for="(detail, code) in selectedEconomy.indicator_details" :key="code" class="flex items-center justify-between bg-bg rounded-lg px-3 py-2">
              <span class="text-xs">{{ tx(detail.name) }}</span>
              <span class="text-xs font-mono" :style="{ color: scoreColor(detail.score) }">{{ detail.score.toFixed(0) }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="text-muted text-center py-12">{{ t('common.noData') }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import client from '@/api/client'
import MetricCard from '@/components/common/MetricCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useI18n } from '@/composables/useI18n'

const scores = ref<any[]>([])
const loading = ref(false)
const selectedEconomy = ref<any>(null)
const { t, tx } = useI18n()

const dimLabels = computed<Record<string, string>>(() => ({
  growth_score: t('ehs.growth'),
  labor_score: t('ehs.labor'),
  price_score: t('ehs.price'),
  external_score: t('ehs.external'),
  financial_score: t('ehs.financial'),
}))

onMounted(() => { loadScores() })

const avgScore = computed(() => {
  if (!scores.value.length) return 0
  return scores.value.reduce((s, e) => s + e.ehs_score, 0) / scores.value.length
})

const recessionCount = computed(() => scores.value.filter(s => s.cycle_phase === 'recession').length)

async function loadScores() {
  loading.value = true
  try {
    const { data } = await client.get('/ehs/scores')
    scores.value = data
  } catch (e: any) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function scoreColor(s: number): string {
  if (s >= 70) return '#2ea043'
  if (s >= 50) return '#d29922'
  if (s >= 35) return '#db6d28'
  return '#f85149'
}

function cycleColor(phase: string): string {
  const map: Record<string, string> = { expansion: '#2ea043', overheating: '#db6d28', slowdown: '#d29922', recession: '#f85149' }
  return map[phase] || '#8b949e'
}

function flagEmoji(code: string): string {
  const flags: Record<string, string> = { US: '🇺🇸', CN: '🇨🇳', EU: '🇪🇺', JP: '🇯🇵', GB: '🇬🇧', DE: '🇩🇪', IN: '🇮🇳', BR: '🇧🇷', KR: '🇰🇷' }
  return flags[code] || '🌐'
}
</script>
