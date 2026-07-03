<template>
  <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 lg:p-5 card-hover">
    <div v-if="loading" class="py-8 text-center text-xs text-[var(--muted)]">{{ t('common.loading') }}</div>
    <div v-else-if="data">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p class="text-[11px] text-[var(--muted)] uppercase tracking-[3px]">{{ t('causal.kicker') }}</p>
          <h3 class="mt-1 text-sm font-medium text-white">{{ t('causal.title') }}</h3>
          <p class="terminal-copy mt-2">{{ t('causal.desc') }}</p>
          <p v-if="data.registry?.persisted" class="mt-2 text-[11px] text-[var(--accent)]">
            {{ t('causal.persisted') }} · {{ data.registry.candidate_count }} {{ t('causal.candidates') }}
          </p>
        </div>
        <div class="grid grid-cols-3 gap-2 sm:min-w-[390px]">
          <div class="terminal-metric">
            <span>{{ t('regime.hidden') }}</span>
            <strong>{{ Number(trigger.hidden_risk || 0).toFixed(0) }}</strong>
          </div>
          <div class="terminal-metric">
            <span>{{ t('regime.damage') }}</span>
            <strong>{{ Number(trigger.realized_damage || 0).toFixed(1) }}</strong>
          </div>
          <div class="terminal-metric">
            <span>{{ t('causal.gap') }}</span>
            <strong :style="{ color: Number(trigger.gap || 0) >= 50 ? 'var(--orange)' : 'var(--muted)' }">{{ Number(trigger.gap || 0).toFixed(0) }}</strong>
          </div>
        </div>
      </div>

      <div class="mt-4 rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
        <div class="mb-3 flex items-center justify-between">
          <p class="text-xs font-medium text-white">{{ t('causal.prompt') }}</p>
          <span class="text-[10px] text-[var(--muted)]">{{ trigger.type }}</span>
        </div>
        <p class="text-[11px] leading-relaxed text-[var(--muted)]">{{ promptTask }}</p>
        <div class="mt-3 flex flex-wrap gap-2">
          <span v-for="rule in promptConstraints" :key="rule" class="rounded border border-[var(--border)] px-2 py-1 text-[10px] text-[var(--muted)]">
            {{ rule }}
          </span>
        </div>
      </div>

      <div class="mt-4 grid gap-4 xl:grid-cols-2">
        <div v-for="item in candidates" :key="item.id" class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-xs font-medium text-white">{{ item.title }}</p>
              <p class="mt-1 text-[11px] leading-relaxed text-[var(--muted)]">{{ item.mechanism }}</p>
            </div>
            <span class="shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-mono"
                  :style="{ color: decisionColor(item.decision), borderColor: decisionColor(item.decision), backgroundColor: decisionColor(item.decision) + '18' }">
              {{ item.graph_status || item.decision }}
            </span>
          </div>

          <div class="mt-3 grid grid-cols-3 gap-2">
            <div class="terminal-metric">
              <span>{{ t('causal.confidence') }}</span>
              <strong>{{ (Number(item.overall_confidence || 0) * 100).toFixed(0) }}%</strong>
            </div>
            <div class="terminal-metric">
              <span>{{ t('causal.graphSupport') }}</span>
              <strong>{{ (Number(item.scores?.graph_support || 0) * 100).toFixed(0) }}%</strong>
            </div>
            <div class="terminal-metric">
              <span>{{ t('causal.dataCoverage') }}</span>
              <strong>{{ (Number(item.scores?.data_coverage || 0) * 100).toFixed(0) }}%</strong>
            </div>
          </div>

          <div class="mt-3 grid gap-3 lg:grid-cols-2">
            <div>
              <p class="mb-2 text-[10px] uppercase tracking-[2px] text-[var(--muted)]">{{ t('causal.tests') }}</p>
              <ul class="space-y-1">
                <li v-for="test in item.observable_tests || []" :key="test" class="text-[11px] leading-relaxed text-[var(--muted)]">• {{ test }}</li>
              </ul>
            </div>
            <div>
              <p class="mb-2 text-[10px] uppercase tracking-[2px] text-[var(--muted)]">{{ t('causal.falsification') }}</p>
              <ul class="space-y-1">
                <li v-for="test in item.falsification || []" :key="test" class="text-[11px] leading-relaxed text-[var(--muted)]">• {{ test }}</li>
              </ul>
            </div>
          </div>

          <p class="mt-3 text-[11px] leading-relaxed text-[var(--accent)]">{{ item.validation_note }}</p>
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

const { t } = useI18n()
const data = ref<any>(null)
const loading = ref(false)

onMounted(load)

async function load() {
  loading.value = true
  try {
    const res = await client.get('/causal-discovery/current')
    data.value = res.data
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
}

const trigger = computed(() => data.value?.trigger || {})
const candidates = computed(() => data.value?.candidate_mechanisms || [])
const promptTask = computed(() => data.value?.ai_prompt?.user_payload?.task || '')
const promptConstraints = computed(() => data.value?.ai_prompt?.user_payload?.constraints || [])

function decisionColor(decision: string): string {
  if (decision === 'eligible_for_promotion') return COLORS.green
  if (decision === 'candidate_graph') return COLORS.accent
  if (decision === 'watchlist') return COLORS.yellow
  return COLORS.red
}
</script>
