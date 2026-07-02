<template>
  <div class="space-y-6">
    <section class="terminal-section">
      <p class="terminal-kicker">GFCRI Governance</p>
      <h1 class="terminal-title">{{ t('trust.title') }}</h1>
      <p class="terminal-copy max-w-3xl">{{ t('trust.subtitle') }}</p>
    </section>

    <section class="grid gap-4 md:grid-cols-2">
      <article class="terminal-card">
        <p class="terminal-kicker">{{ t('trust.methodology') }}</p>
        <p class="terminal-copy mt-3">{{ t('trust.methodologyBody') }}</p>
      </article>
      <article class="terminal-card">
        <p class="terminal-kicker">{{ t('trust.sources') }}</p>
        <p class="terminal-copy mt-3">{{ t('trust.sourcesBody') }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <span class="terminal-chip">FRED</span>
          <span class="terminal-chip">yfinance</span>
          <span class="terminal-chip">OECD</span>
          <span class="terminal-chip">AKShare</span>
          <span class="terminal-chip">Public market data</span>
        </div>
      </article>
      <article class="terminal-card">
        <p class="terminal-kicker">{{ t('trust.limitations') }}</p>
        <p class="terminal-copy mt-3">{{ t('trust.limitationsBody') }}</p>
      </article>
      <article class="terminal-card">
        <p class="terminal-kicker">{{ t('trust.disclaimer') }}</p>
        <p class="terminal-copy mt-3">{{ t('trust.disclaimerBody') }}</p>
      </article>
    </section>

    <section class="terminal-card">
      <p class="terminal-kicker">Model Transparency</p>
      <div class="mt-4 grid gap-3 md:grid-cols-4">
        <div class="terminal-metric">
          <span>{{ t('dash.indicatorCount') }}</span>
          <strong>38</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ t('dash.chainCount') }}</span>
          <strong>12</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ t('dash.dataCadence') }}</span>
          <strong>06:00 UTC</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ t('dash.modelVersion') }}</span>
          <strong>GFCRI v1</strong>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()
</script>
