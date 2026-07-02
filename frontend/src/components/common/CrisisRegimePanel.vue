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
                  :style="{ color: levelColor, borderColor: levelColor, backgroundColor: levelColor + '18' }">
              L{{ assessment.level.level }} · {{ levelLabel(assessment.level) }}
            </span>
          </div>
          <p class="terminal-copy mt-2">{{ assessment.interpretation }}</p>
        </div>
        <div class="grid grid-cols-2 gap-2 sm:min-w-[260px]">
          <div class="terminal-metric">
            <span>{{ t('regime.score') }}</span>
            <strong :style="{ color: levelColor }">{{ Number(assessment.score || 0).toFixed(1) }}</strong>
          </div>
          <div class="terminal-metric">
            <span>{{ t('regime.progress') }}</span>
            <strong>{{ Number(assessment.level_progress || 0).toFixed(0) }}%</strong>
          </div>
        </div>
      </div>

      <div class="mt-4 h-2 overflow-hidden rounded-full bg-white/[0.05]">
        <div class="h-full rounded-full transition-all" :style="{ width: regimeWidth, backgroundColor: levelColor }"></div>
      </div>
      <div class="mt-2 grid grid-cols-5 gap-1 text-[9px] text-[var(--muted)]">
        <span v-for="level in assessment.levels" :key="level.id" class="truncate">{{ levelLabel(level) }}</span>
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
        <p class="mb-3 text-xs font-medium text-white">{{ t('regime.reference') }}</p>
        <div class="grid gap-3 lg:grid-cols-2">
          <div v-for="level in assessment.levels" :key="level.id" class="rounded-lg border border-[var(--border)] p-3">
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

defineProps<{ compact?: boolean }>()

const { t, lang } = useI18n()
const assessment = ref<any>(null)
const loading = ref(false)

onMounted(loadAssessment)

async function loadAssessment() {
  loading.value = true
  try {
    const { data } = await client.get('/regime-assessment/latest')
    assessment.value = data
  } catch (e) {
    assessment.value = null
  } finally {
    loading.value = false
  }
}

const visibleFactors = computed(() => (assessment.value?.factors || []).slice(0, 8))
const visibleMatches = computed(() => (assessment.value?.matches || []).slice(0, 3))
const levelColor = computed(() => factorColor(Number(assessment.value?.score || 0)))
const regimeWidth = computed(() => `${Math.min(Number(assessment.value?.score || 0), 100)}%`)

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

function matchName(match: any): string {
  return lang.value === 'zh' ? match.name_zh || match.name : match.name
}
</script>
