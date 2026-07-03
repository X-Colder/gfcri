<template>
  <div class="space-y-6">
    <section class="terminal-section fade-in">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p class="terminal-kicker">{{ t('institutional.kicker') }}</p>
          <h1 class="terminal-title">{{ t('institutional.title') }}</h1>
          <p class="terminal-copy mt-2 max-w-3xl">{{ t('institutional.subtitle') }}</p>
        </div>
        <div class="grid grid-cols-3 gap-2 xl:min-w-[420px]">
          <div class="terminal-metric">
            <span>{{ t('institutional.output') }}</span>
            <strong>4</strong>
          </div>
          <div class="terminal-metric">
            <span>{{ t('institutional.delivery') }}</span>
            <strong>API</strong>
          </div>
          <div class="terminal-metric">
            <span>{{ t('institutional.deploy') }}</span>
            <strong>Private</strong>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.9fr)]">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5">
        <p class="terminal-kicker">{{ t('institutional.workflows') }}</p>
        <h2 class="mt-1 text-base font-medium text-white">{{ t('institutional.workflowTitle') }}</h2>
        <div class="mt-5 grid gap-3 md:grid-cols-2">
          <div v-for="item in workflows" :key="item.title" class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
            <p class="text-sm font-medium text-white">{{ item.title }}</p>
            <p class="mt-2 text-xs leading-relaxed text-[var(--muted)]">{{ item.desc }}</p>
            <div class="mt-3 flex flex-wrap gap-1.5">
              <span v-for="tag in item.tags" :key="tag" class="rounded border border-[var(--border)] px-2 py-0.5 text-[10px] text-[var(--muted)]">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-5">
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5">
          <p class="terminal-kicker">{{ t('institutional.package') }}</p>
          <div class="mt-4 space-y-3">
            <div v-for="item in packageItems" :key="item" class="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-white/[0.012] px-3 py-2">
              <span class="h-1.5 w-1.5 rounded-full bg-[var(--accent)]"></span>
              <span class="text-xs text-white">{{ item }}</span>
            </div>
          </div>
        </div>

        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5">
          <p class="terminal-kicker">{{ t('institutional.positioning') }}</p>
          <p class="mt-3 text-xs leading-relaxed text-[var(--muted)]">{{ t('institutional.positioningBody') }}</p>
        </div>
      </div>
    </section>

    <CrisisRegimePanel />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '@/composables/useI18n'
import CrisisRegimePanel from '@/components/common/CrisisRegimePanel.vue'

const { t } = useI18n()

const workflows = computed(() => [
  {
    title: t('institutional.researchDesk'),
    desc: t('institutional.researchDeskDesc'),
    tags: ['Daily Brief', 'Backtest', 'Risk Drivers'],
  },
  {
    title: t('institutional.advisorDesk'),
    desc: t('institutional.advisorDeskDesc'),
    tags: ['Client Talking Points', 'Risk Cards', 'Scenario Explain'],
  },
  {
    title: t('institutional.riskDesk'),
    desc: t('institutional.riskDeskDesc'),
    tags: ['Damage Level', 'Hidden Risk', 'Transmission'],
  },
  {
    title: t('institutional.integration'),
    desc: t('institutional.integrationDesc'),
    tags: ['API', 'Private Deploy', 'White Label'],
  },
])

const packageItems = computed(() => [
  t('institutional.pkg1'),
  t('institutional.pkg2'),
  t('institutional.pkg3'),
  t('institutional.pkg4'),
  t('institutional.pkg5'),
])
</script>
