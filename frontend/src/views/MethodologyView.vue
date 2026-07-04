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

    <section class="terminal-card">
      <p class="terminal-kicker">{{ t('trust.coverageAudit') }}</p>
      <div class="mt-4 grid gap-3 md:grid-cols-4">
        <div class="terminal-metric">
          <span>{{ t('dash.indicatorCount') }}</span>
          <strong>{{ coverageSummary?.node_count ?? '-' }}</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ t('trust.tierABShare') }}</span>
          <strong>{{ coverageSummary?.tier_a_b_share ?? '-' }}%</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ t('trust.proxyLowTier') }}</span>
          <strong>{{ coverageSummary?.proxy_or_low_tier_count ?? '-' }}</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ t('dash.modelVersion') }}</span>
          <strong>Audit v1</strong>
        </div>
      </div>
      <p class="terminal-copy mt-4">{{ coverageSummary?.professional_standard || t('trust.sourcesBody') }}</p>
      <div class="mt-4 grid gap-3 lg:grid-cols-[0.75fr_1.25fr]">
        <div class="method-block">
          <p class="text-sm text-white font-medium">{{ t('trust.sourceTierMix') }}</p>
          <div class="mt-3 space-y-2">
            <div v-for="(count, tier) in coverageSummary?.source_tier_counts || {}" :key="tier" class="flex items-center justify-between text-xs">
              <span class="text-[var(--muted)]">Tier {{ tier }}</span>
              <strong class="font-mono text-white">{{ count }}</strong>
            </div>
          </div>
        </div>
        <div class="method-block">
          <p class="text-sm text-white font-medium">{{ t('trust.upgradePriorities') }}</p>
          <div class="mt-3 max-h-[260px] overflow-y-auto">
            <div v-for="item in upgradePriorities" :key="item.node_id" class="border-t border-[var(--border)] py-2 first:border-t-0">
              <div class="flex items-center justify-between gap-3">
                <p class="text-xs text-white">{{ item.display_name }}</p>
                <span class="rounded border border-[var(--border)] px-2 py-0.5 text-[10px] text-[var(--muted)]">Tier {{ item.source_tier }}</span>
              </div>
              <p class="mt-1 text-[11px] leading-relaxed text-[var(--muted)]">{{ item.upgrade_plan || item.reason }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="terminal-card">
      <p class="terminal-kicker">{{ t('institutional.causalRigor') }}</p>
      <div class="mt-4 grid gap-3 md:grid-cols-3">
        <div class="terminal-metric">
          <span>Candidate Edges</span>
          <strong>{{ readiness?.causal_validation?.candidate_count ?? '-' }}</strong>
        </div>
        <div class="terminal-metric">
          <span>Validated</span>
          <strong>{{ readiness?.causal_validation?.validated_count ?? '-' }}</strong>
        </div>
        <div class="terminal-metric">
          <span>Promotion Ready</span>
          <strong>{{ readiness?.causal_validation?.promotion_ready_count ?? '-' }}</strong>
        </div>
      </div>
      <p class="terminal-copy mt-4">{{ readiness?.causal_validation?.methodology || t('causal.desc') }}</p>
      <div class="mt-4 overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="text-[var(--muted)] border-b border-[var(--border)]">
              <th class="text-left py-2 pr-3">Candidate</th>
              <th class="text-left py-2 px-3">Stage</th>
              <th class="text-right py-2 pl-3">Score</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in causalRows" :key="row.candidate_id" class="border-b border-[var(--border)]/40">
              <td class="py-2 pr-3 text-white">{{ row.title }}</td>
              <td class="py-2 px-3 text-[var(--muted)]">{{ row.stage }}</td>
              <td class="py-2 pl-3 text-right font-mono">{{ Math.round(row.validation_score * 100) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="terminal-card">
      <p class="terminal-kicker">{{ t('trust.formulas') }}</p>
      <div class="mt-4 grid gap-3 lg:grid-cols-2">
        <div v-for="item in formulas" :key="item.name" class="method-block">
          <p class="text-sm text-white font-medium">{{ item.name }}</p>
          <code class="method-code">{{ item.formula }}</code>
          <p class="terminal-copy mt-2">{{ item.note }}</p>
        </div>
      </div>
    </section>

    <section class="terminal-card">
      <p class="terminal-kicker">{{ t('trust.weights') }}</p>
      <div class="mt-4 overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="text-[var(--muted)] border-b border-[var(--border)]">
              <th class="text-left py-2 pr-3">{{ t('analysis.subIndexBreakdown') }}</th>
              <th class="text-right py-2 px-3">{{ t('trust.weight') }}</th>
              <th class="text-left py-2 pl-3">Nodes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in weights" :key="row.id" class="border-b border-[var(--border)]/40">
              <td class="py-2 pr-3 text-white">{{ row.name }}</td>
              <td class="py-2 px-3 text-right font-mono">{{ row.weight }}</td>
              <td class="py-2 pl-3 text-[var(--muted)]">{{ row.nodes }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="terminal-card">
      <p class="terminal-kicker">{{ t('trust.thresholds') }}</p>
      <div class="mt-4 overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="text-[var(--muted)] border-b border-[var(--border)]">
              <th class="text-left py-2 pr-3">{{ t('analysis.node') }}</th>
              <th class="text-right py-2 px-3">{{ t('trust.normal') }}</th>
              <th class="text-right py-2 px-3">{{ t('trust.crisisThreshold') }}</th>
              <th class="text-left py-2 pl-3">{{ t('trust.direction') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in thresholds" :key="row.node" class="border-b border-[var(--border)]/40">
              <td class="py-2 pr-3 text-white">{{ row.node }}</td>
              <td class="py-2 px-3 text-right font-mono">{{ row.normal }}</td>
              <td class="py-2 px-3 text-right font-mono">{{ row.crisis }}</td>
              <td class="py-2 pl-3 text-[var(--muted)]">{{ row.direction }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="terminal-card">
      <p class="terminal-kicker">{{ t('trust.riskChains') }}</p>
      <div class="mt-4 grid gap-3 lg:grid-cols-2">
        <div v-for="chain in chains" :key="chain.name" class="method-block">
          <p class="text-sm text-white font-medium">{{ chain.name }}</p>
          <p class="text-[11px] text-[var(--muted)] font-mono mt-1">{{ chain.path }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from '@/composables/useI18n'
import { fetchModelFoundation } from '@/api/modelFoundation'
import { fetchCommercialReadiness } from '@/api/commercialReadiness'
import type { ModelFoundation } from '@/api/types'

const { t, tx } = useI18n()
const foundation = ref<ModelFoundation | null>(null)
const readiness = ref<any | null>(null)

onMounted(async () => {
  try {
    foundation.value = await fetchModelFoundation()
  } catch {
    foundation.value = null
  }
  try {
    readiness.value = await fetchCommercialReadiness()
  } catch {
    readiness.value = null
  }
})

const coverageSummary = computed(() => foundation.value?.coverage_summary || null)
const upgradePriorities = computed(() => foundation.value?.upgrade_priorities || [])
const causalRows = computed(() => readiness.value?.causal_validation?.candidates?.slice(0, 8) ?? [])

const formulas = [
  {
    name: 'Indicator anomaly',
    formula: 'Anomaly Score = min(1.0, abs(Z-score) / 4.0)',
    note: 'Captures fast deviations from recent historical behavior.',
  },
  {
    name: 'Sub-index stress',
    formula: 'Sub-index = 100 x (0.6 x raw stress + 0.4 x transmission)',
    note: 'Combines anomaly stress, absolute stress, and external transmission pressure.',
  },
  {
    name: 'Transmission channel',
    formula: 'Chain Stress = average(node anomaly scores) x 100',
    note: 'Shows whether linked indicators are becoming stressed together.',
  },
  {
    name: 'Final GFCRI',
    formula: 'GFCRI = weighted base x signal coherence + hidden risk boost + trade spillover boost',
    note: 'Adds synchronization, hidden-risk, and cross-economy trade-spillover effects to the weighted base score.',
  },
]

const weights = [
  { id: 'SI_RATES', name: tx('利率与央行'), weight: '14%', nodes: 'fed_funds, ust_10y, ust_2y' },
  { id: 'SI_FX', name: tx('全球汇率'), weight: '14%', nodes: 'dxy, krw_usd, eurusd, cny_usd, jpy_usd' },
  { id: 'SI_US_EQUITY', name: tx('美国股市'), weight: '10%', nodes: 'spx, sox' },
  { id: 'SI_ASIA_EQUITY', name: tx('亚洲股市'), weight: '10%', nodes: 'kospi, hsi, nikkei' },
  { id: 'SI_EUROPE', name: tx('欧洲市场'), weight: '8%', nodes: 'stoxx50, italy_etf' },
  { id: 'SI_CREDIT', name: tx('信用与违约'), weight: '14%', nodes: 'hyg, lqd, kr_cds_5y, orcl_cds, emb' },
  { id: 'SI_BANKING', name: tx('银行与房产'), weight: '8%', nodes: 'kre, vnq' },
  { id: 'SI_COMMODITY', name: tx('商品与贸易'), weight: '10%', nodes: 'oil_wti, copper, gold, natgas, wheat, dram, nand, bdry' },
  { id: 'SI_SENTIMENT', name: tx('情绪与风险偏好'), weight: '12%', nodes: 'vix, recession_prob, btc, consumer_stress, eem' },
  { id: 'SI_TRADE_SPILLOVER', name: tx('贸易依赖传导'), weight: 'Additive, max +8 pts', nodes: 'static-v1 trade dependency matrix' },
]

const thresholds = [
  { node: 'VIX', normal: '15', crisis: '45', direction: 'Higher is worse' },
  { node: 'DXY', normal: '100', crisis: '114', direction: 'Higher is worse' },
  { node: 'S&P 500', normal: '5000', crisis: '3500', direction: 'Lower is worse' },
  { node: 'US 10Y Treasury', normal: '3.5', crisis: '5.2', direction: 'Higher is worse' },
  { node: 'WTI Crude', normal: '70', crisis: '120', direction: 'Higher is worse' },
  { node: 'KRW/USD', normal: '1250', crisis: '1550', direction: 'Higher is worse' },
  { node: 'KOSPI', normal: '2600', crisis: '1800', direction: 'Lower is worse' },
  { node: 'Hang Seng', normal: '22000', crisis: '14000', direction: 'Lower is worse' },
]

const chains = [
  { name: tx('央行加息冲击波'), path: 'Fed Funds -> US 10Y -> DXY -> KRW/USD' },
  { name: tx('强美元挤压'), path: 'US 10Y -> DXY -> KRW/USD -> KOSPI' },
  { name: tx('信用危机传染'), path: 'LQD -> HYG -> Korea CDS -> KOSPI' },
  { name: tx('房地产银行危机'), path: 'VNQ -> KRE -> VIX' },
  { name: tx('中国冲击波'), path: 'USD/CNY -> Hang Seng -> KOSPI' },
  { name: tx('欧债危机传染'), path: 'Italy ETF -> EUR/USD -> DXY -> EEM' },
  { name: tx('日元套利平仓'), path: 'USD/JPY -> Nikkei -> VIX' },
  { name: tx('粮食能源冲击'), path: 'Wheat -> Natural Gas -> Euro Stoxx 50' },
]
</script>

<style scoped>
.method-block {
  background: rgba(255,255,255,0.015);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
}

.method-code {
  display: block;
  margin-top: 8px;
  white-space: normal;
}
</style>
