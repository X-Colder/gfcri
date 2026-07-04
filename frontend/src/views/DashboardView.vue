<template>
  <div class="dashboard-root">
    <!-- Noise/grain texture overlay -->
    <div class="noise-overlay" aria-hidden="true"></div>

    <LoadingSpinner v-if="riskStore.loading" />

    <template v-else-if="riskStore.latest">

      <section class="command-center terminal-section fade-in">
        <div class="command-topbar">
          <div>
            <p class="terminal-kicker">{{ t('dash.eyebrow') }}</p>
            <h1 class="terminal-title">{{ t('dash.title') }}</h1>
            <p class="terminal-copy mt-2">{{ t('dash.subtitle') }}</p>
          </div>
          <div class="command-meta">
            <div class="command-meta-cell">
              <span>{{ t('dash.latestObservation') }}</span>
              <strong>{{ riskStore.latest.index_date }}</strong>
            </div>
            <div class="command-meta-cell">
              <span>{{ t('dash.dataCadence') }}</span>
              <strong>06:00 UTC</strong>
            </div>
            <div class="command-meta-cell">
              <span>{{ t('dash.modelVersion') }}</span>
              <strong>GFCRI v1</strong>
            </div>
          </div>
        </div>

        <div class="command-grid">
          <aside class="score-console">
            <div class="score-console-head">
              <div>
                <p class="terminal-kicker">GFCRI</p>
                <div class="risk-score-row">
                  <span class="risk-score" :style="{ color: getAlertColor(riskStore.latest.alert_level) }">
                    {{ riskStore.latest.gfcri_value.toFixed(1) }}
                  </span>
                  <span class="risk-alert" :style="{ color: getAlertColor(riskStore.latest.alert_level), borderColor: getAlertColor(riskStore.latest.alert_level), backgroundColor: getAlertColor(riskStore.latest.alert_level) + '12' }">
                    {{ t('alert.' + riskStore.latest.alert_level) }}
                  </span>
                </div>
              </div>
              <span class="score-delta" :class="trendDelta >= 0 ? 'score-delta-up' : 'score-delta-down'">
                {{ trendDelta >= 0 ? '+' : '' }}{{ trendDelta.toFixed(1) }} 30D
              </span>
            </div>
            <p class="terminal-copy score-summary">{{ heroSummary }}</p>

            <div class="regime-stack">
              <div class="regime-line">
                <span>{{ t('regime.damage') }}</span>
                <strong>{{ currentDamageLabel }}</strong>
              </div>
              <div class="regime-line">
                <span>{{ t('regime.pressure') }}</span>
                <strong :style="{ color: getAlertColor(riskStore.latest.alert_level) }">{{ t('alert.' + riskStore.latest.alert_level) }}</strong>
              </div>
              <div class="regime-line">
                <span>{{ t('regime.hidden') }}</span>
                <strong :style="{ color: hiddenRiskColor }">{{ hiddenRiskSummary.status }}</strong>
              </div>
            </div>

            <div class="score-actions">
              <router-link to="/analysis">{{ t('dash.openAnalysis') }}</router-link>
              <router-link to="/methodology">{{ t('nav.methodology') }}</router-link>
            </div>
          </aside>

          <main class="decision-console">
            <div class="console-head">
              <div>
                <p class="terminal-kicker">{{ t('dash.commandBrief') }}</p>
                <h2 class="terminal-subtitle">{{ t('dash.dailyWorkbench') }}</h2>
              </div>
              <router-link to="/analysis" class="receipt-link">{{ t('analysis.unlockChain') }}</router-link>
            </div>

            <div class="judgment-band">
              <span class="judgment-status" :style="{ color: getAlertColor(riskStore.latest.alert_level) }">
                {{ t('alert.' + riskStore.latest.alert_level) }}
              </span>
              <p>{{ heroSummary }}</p>
            </div>

            <div class="evidence-grid">
              <div class="evidence-cell">
                <span>{{ t('dash.weightedBase') }}</span>
                <strong>{{ scoreReceipt.weightedBase.toFixed(1) }}</strong>
              </div>
              <div class="evidence-cell">
                <span>{{ t('dash.coherence') }}</span>
                <strong>{{ scoreReceipt.coherence.toFixed(2) }}x</strong>
              </div>
              <div class="evidence-cell">
                <span>{{ t('dash.hiddenRiskBoost') }}</span>
                <strong :style="{ color: hiddenRiskColor }">+{{ scoreReceipt.hiddenBoost.toFixed(1) }}</strong>
              </div>
              <div class="evidence-cell">
                <span>{{ t('dash.tradeBoost') }}</span>
                <strong>+{{ scoreReceipt.tradeBoost.toFixed(1) }}</strong>
              </div>
              <div class="evidence-cell">
                <span>{{ t('dash.marketBreadth') }}</span>
                <strong>{{ anomalyCount }}</strong>
              </div>
              <div class="evidence-cell">
                <span>{{ t('dash.transmissionState') }}</span>
                <strong>{{ activeChainCount }}</strong>
              </div>
            </div>

            <div class="console-split">
              <section class="driver-board">
                <div class="board-head">
                  <p class="terminal-kicker">{{ t('dash.topEvidence') }}</p>
                  <span>{{ t('dash.primaryDriver') }}: {{ primaryDriver }}</span>
                </div>
                <div class="driver-table">
                  <div class="driver-table-row driver-table-head">
                    <span>{{ t('analysis.indicator') }}</span>
                    <span>{{ t('analysis.current') }}</span>
                    <span>{{ t('analysis.zscore') }}</span>
                    <span>{{ t('analysis.absScore') }}</span>
                  </div>
                  <div v-for="driver in topDrivers" :key="driver.id" class="driver-table-row">
                    <span class="driver-label">{{ driver.name }}</span>
                    <span>{{ driver.current }}</span>
                    <span :style="{ color: driver.pressure > 0 ? COLORS.orange : 'var(--muted)' }">{{ driver.zscore.toFixed(2) }}</span>
                    <span>{{ driver.absScore }}</span>
                  </div>
                </div>
              </section>

              <section class="risk-queue">
                <div class="queue-item queue-next">
                  <span>{{ t('dash.nextWatch') }}</span>
                  <p>{{ nextWatchText }}</p>
                </div>
                <div class="queue-item">
                  <span>{{ t('analysis.hiddenRisk') }}</span>
                  <strong :style="{ color: hiddenRiskColor }">{{ hiddenRiskSummary.status }}</strong>
                  <p>{{ hiddenRiskSummary.detail }}</p>
                </div>
                <div class="queue-item">
                  <span>{{ t('dash.transmissionState') }}</span>
                  <strong>{{ activeChainCount }} {{ t('analysis.chainActive') }}</strong>
                  <p>{{ topChain }}</p>
                </div>
              </section>
            </div>
          </main>

          <aside class="command-right-rail">
            <div v-if="riskStore.history.length > 1" class="trend-panel">
              <div class="section-head">
                <div>
                  <p class="terminal-kicker">{{ t('dash.trendWindow') }}</p>
                  <h2 class="terminal-subtitle">{{ t('analysis.trend') }}</h2>
                </div>
                <span class="text-[10px] text-[var(--muted)] font-mono">30D</span>
              </div>
              <v-chart :option="trendChartOption" style="height: 230px" autoresize />
            </div>
            <RiskWatch compact class="mt-4" />
          </aside>
        </div>

        <div class="score-receipt compact-receipt">
          <div class="receipt-head">
            <div>
              <p class="terminal-kicker">{{ t('dash.scoreReceipt') }}</p>
              <p class="terminal-copy mt-1">{{ t('dash.scoreFormula') }}</p>
            </div>
            <router-link to="/methodology" class="receipt-link">{{ t('nav.methodology') }}</router-link>
          </div>
          <div class="receipt-grid">
            <div class="receipt-step">
              <span>{{ t('dash.weightedBase') }}</span>
              <strong>{{ scoreReceipt.weightedBase.toFixed(1) }}</strong>
            </div>
            <div class="receipt-op">×</div>
            <div class="receipt-step">
              <span>{{ t('dash.coherence') }}</span>
              <strong>{{ scoreReceipt.coherence.toFixed(2) }}</strong>
            </div>
            <div class="receipt-op">+</div>
            <div class="receipt-step">
              <span>{{ t('dash.hiddenRiskBoost') }}</span>
              <strong>+{{ scoreReceipt.hiddenBoost.toFixed(1) }}</strong>
            </div>
            <div class="receipt-op">+</div>
            <div class="receipt-step">
              <span>{{ t('dash.tradeBoost') }}</span>
              <strong>+{{ scoreReceipt.tradeBoost.toFixed(1) }}</strong>
            </div>
            <div class="receipt-op">=</div>
            <div class="receipt-step receipt-final">
              <span>{{ t('dash.finalScore') }}</span>
              <strong :style="{ color: getAlertColor(riskStore.latest.alert_level) }">{{ riskStore.latest.gfcri_value.toFixed(1) }}</strong>
            </div>
          </div>
        </div>

        <div class="model-lens-grid">
          <CrisisRegimePanel compact />
          <TradeSpilloverPanel compact />
        </div>
      </section>

      <!-- ── Signal Cards ── -->
      <Paywall :blurred="!isPro" :title="t('dash.anomalous')" :description="t('common.upgradeDesc')">
      <div class="cards-grid fade-in fade-in-delay-1">

        <!-- Anomalous Indicators -->
        <div
          class="signal-card"
          :class="anomalyCount > 5 ? 'card--danger' : 'card--safe'"
          :style="{ '--card-accent': anomalyCount > 5 ? COLORS.red : COLORS.green }"
        >
          <div class="card-gradient" aria-hidden="true"></div>
          <p class="card-label">{{ t('dash.anomalous') }}</p>
          <p
            class="card-value count-up"
            :data-target="anomalyCount"
            :style="{ color: anomalyCount > 5 ? COLORS.red : COLORS.green }"
          >{{ anomalyCount }}</p>
          <p class="card-detail">{{ topAnomalies }}</p>
        </div>

        <!-- Active Chains -->
        <div
          class="signal-card"
          :class="activeChainCount >= 4 ? 'card--warning' : 'card--safe'"
          :style="{ '--card-accent': activeChainCount >= 4 ? COLORS.orange : COLORS.green }"
        >
          <div class="card-gradient" aria-hidden="true"></div>
          <p class="card-label">{{ t('dash.chains') }}</p>
          <p
            class="card-value"
            :style="{ color: activeChainCount >= 4 ? COLORS.orange : COLORS.green }"
          >{{ activeChainCount }}</p>
          <p class="card-detail">{{ topChain }}</p>
        </div>

        <!-- Coherence -->
        <div
          class="signal-card card--accent"
          :style="{ '--card-accent': COLORS.accent }"
        >
          <div class="card-gradient" aria-hidden="true"></div>
          <p class="card-label">{{ t('dash.coherence') }}</p>
          <p class="card-value" style="color: var(--accent)">
            {{ (riskStore.latest.coherence_multiplier || 1).toFixed(2) }}×
          </p>
          <p class="card-detail">
            {{ (riskStore.latest.coherence_multiplier || 1) > 1.1 ? t('dash.multiChain') : t('dash.independent') }}
          </p>
        </div>
      </div>
      </Paywall>

      <!-- ── Global Risk Network Globe ── -->
      <div class="fade-in fade-in-delay-2" style="margin-bottom: 32px;">
        <GlobeNetwork />
      </div>

      <!-- ── Trust Bar ── -->
      <div class="trust-bar fade-in fade-in-delay-2">
        <div class="trust-separator" aria-hidden="true"></div>
        <p class="trust-powered">{{ t('dash.powered') }}</p>
        <div class="trust-sources">
          <span class="trust-item">{{ t('dash.indicatorCount') }}</span>
          <span class="trust-dot" aria-hidden="true">·</span>
          <span class="trust-item">{{ t('dash.chainCount') }}</span>
          <span class="trust-dot" aria-hidden="true">·</span>
          <span class="trust-item">FRED</span>
          <span class="trust-dot" aria-hidden="true">·</span>
          <span class="trust-item">yfinance</span>
          <span class="trust-dot" aria-hidden="true">·</span>
          <span class="trust-item">AKShare</span>
          <span class="trust-dot" aria-hidden="true">·</span>
          <span class="trust-item">AI-assisted narrative</span>
        </div>
        <p class="trust-note">{{ t('dash.methodologyShort') }}</p>
      </div>

    </template>

    <div v-else class="empty-state">{{ t('common.noData') }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { useRiskStore } from '@/stores/risk'
import { COLORS, getAlertColor } from '@/composables/useTheme'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Paywall from '@/components/common/Paywall.vue'
import GlobeNetwork from '@/components/charts/GlobeNetwork.vue'
import TradeSpilloverPanel from '@/components/common/TradeSpilloverPanel.vue'
import CrisisRegimePanel from '@/components/common/CrisisRegimePanel.vue'
import RiskWatch from '@/components/common/RiskWatch.vue'

use([LineChart, GridComponent, TooltipComponent, MarkLineComponent, CanvasRenderer])

const riskStore = useRiskStore()
const { isPro } = useAuth()
const { t, tx } = useI18n()

onMounted(() => {
  riskStore.loadLatest()
  riskStore.loadHistory()
})

const anomalyCount = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return 0
  return Object.values(nc).filter((n: any) => n.is_anomalous).length
})

const activeChainCount = computed(() => {
  const chains = riskStore.latest?.chain_details
  if (!chains) return 0
  const list = Array.isArray(chains) ? chains : Object.values(chains)
  return list.filter((c: any) => c.active).length
})

const topAnomalies = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return ''
  const items = Object.entries(nc)
    .filter(([, info]: [string, any]) => info.is_anomalous)
    .sort((a: any, b: any) => Math.abs(b[1].zscore) - Math.abs(a[1].zscore))
    .slice(0, 3)
    .map(([, info]: [string, any]) => tx(info.display_name))
  return items.join(' · ') || '—'
})

const topChain = computed(() => {
  const chains = riskStore.latest?.chain_details
  if (!chains) return '—'
  const list = Array.isArray(chains) ? chains : Object.values(chains)
  const active = list.filter((c: any) => c.active).sort((a: any, b: any) => b.stress - a.stress)
  return active.length > 0 ? tx(active[0].name) : t('dash.noActiveChain')
})

const primaryDriver = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return t('dash.noDriver')
  const item = Object.entries(nc)
    .sort((a: any, b: any) => driverSortScore(b[1]) - driverSortScore(a[1]))[0]
  if (!item) return t('dash.noDriver')
  return tx((item[1] as any).display_name || item[0])
})

const primaryDriverDetail = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return '—'
  const item = Object.entries(nc)
    .sort((a: any, b: any) => driverSortScore(b[1]) - driverSortScore(a[1]))[0]
  if (!item) return '—'
  const info: any = item[1]
  const z = Number(info.zscore || 0)
  const abs = info.abs_score === null || info.abs_score === undefined ? null : Number(info.abs_score)
  const absText = abs === null ? '-' : `${(abs * 100).toFixed(0)}`
  return `Z ${z.toFixed(2)} · ${t('analysis.anomalyScore')} ${((Number(info.anomaly_score || 0)) * 100).toFixed(0)} · ${t('analysis.absScore')} ${absText}`
})

const topDrivers = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return []
  return Object.entries(nc)
    .map(([id, info]: [string, any]) => ({
      id,
      name: tx(info.display_name || id),
      current: formatCurrentValue(info.current_value),
      zscore: Number(info.zscore || 0),
      pressure: Number(info.anomaly_score || 0) * 100,
      absScore: info.abs_score === null || info.abs_score === undefined
        ? '-'
        : (Number(info.abs_score) * 100).toFixed(0),
      sortScore: driverSortScore(info),
    }))
    .sort((a, b) => b.sortScore - a.sortScore)
    .slice(0, 5)
})

function driverSortScore(info: any): number {
  const anomaly = Number(info?.anomaly_score || 0)
  const abs = info?.abs_score === null || info?.abs_score === undefined ? 0 : Number(info.abs_score)
  return Math.max(anomaly, abs)
}

const currentDamageLabel = computed(() => {
  const score = riskStore.latest?.gfcri_value || 0
  if (score >= 75) return 'D4+'
  if (score >= 55) return 'D2-D3?'
  if (score >= 40) return 'D0 / D1'
  if (score >= 25) return 'D0'
  return 'D0'
})

const nextWatchText = computed(() => {
  if (scoreReceipt.value.hiddenBoost >= 15) return t('dash.watchHidden')
  if (activeChainCount.value >= 4) return t('dash.watchTransmission')
  if (anomalyCount.value >= 6) return t('dash.watchAnomalies')
  return t('dash.watchNormal')
})

const hiddenRiskSummary = computed(() => {
  const risk = riskStore.latest
  const divergence = risk?.divergence || {}
  const status = String(divergence.status || hiddenStatusFromBoost(scoreReceipt.value.hiddenBoost))
  const rawDetails = Array.isArray(divergence.details) ? divergence.details : []
  const first = rawDetails[0]
  const detail = first
    ? hiddenDetailText(first)
    : scoreReceipt.value.hiddenBoost > 0
      ? t('dash.hiddenRiskDetected', { boost: scoreReceipt.value.hiddenBoost.toFixed(1) })
      : t('analysis.hiddenNone')
  return {
    status: hiddenRiskStatusLabel(status),
    detail,
  }
})

const hiddenRiskColor = computed(() => {
  const status = String(riskStore.latest?.divergence?.status || hiddenStatusFromBoost(scoreReceipt.value.hiddenBoost))
  if (status === 'critical') return COLORS.red
  if (status === 'significant') return COLORS.orange
  if (status === 'mild') return COLORS.yellow
  return COLORS.green
})

const SUB_INDEX_WEIGHTS: Record<string, number> = {
  SI_RATES: 0.14,
  SI_FX: 0.14,
  SI_US_EQUITY: 0.10,
  SI_ASIA_EQUITY: 0.10,
  SI_EUROPE: 0.08,
  SI_CREDIT: 0.14,
  SI_BANKING: 0.08,
  SI_COMMODITY: 0.10,
  SI_SENTIMENT: 0.12,
  SI_TRADE_SPILLOVER: 0,
}

const scoreReceipt = computed(() => {
  const details = riskStore.latest?.sub_index_details || {}
  const weightedBase = Object.entries(details).reduce((sum, [key, val]: [string, any]) => {
    return sum + Number(val?.score || 0) * (SUB_INDEX_WEIGHTS[key] || 0)
  }, 0)
  return {
    weightedBase,
    coherence: riskStore.latest?.coherence_multiplier || 1,
    hiddenBoost: riskStore.latest?.undercurrent_boost || 0,
    tradeBoost: riskStore.latest?.trade_spillover_boost || 0,
  }
})

const heroSummary = computed(() => {
  const ac = activeChainCount.value
  const an = anomalyCount.value
  if (an > 8 && ac >= 5) return t('dash.summary.high', { an, ac })
  if (ac >= 5) return t('dash.summary.chains', { ac })
  if (an > 5) return t('dash.summary.anomaly', { an })
  return t('dash.summary.normal')
})

const trendDelta = computed(() => {
  const data = riskStore.history
  if (data.length < 2) return 0
  const latest = Number(riskStore.latest?.gfcri_value ?? data[0]?.gfcri_value ?? 0)
  const oldest = Number(data[data.length - 1]?.gfcri_value ?? latest)
  return latest - oldest
})

const trendChartOption = computed(() => {
  const data = [...riskStore.history].reverse()
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#111214',
      borderColor: 'rgba(255,255,255,0.06)',
      textStyle: { color: '#eff1f5', fontSize: 12 },
    },
    grid: { left: 42, right: 18, top: 20, bottom: 28 },
    xAxis: { type: 'category', data: data.map(d => d.index_date), axisLabel: { color: '#6b7280', fontSize: 10 } },
    yAxis: {
      type: 'value', min: 0, max: 100,
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
      axisLabel: { color: '#6b7280', fontSize: 10 },
    },
    series: [{
      type: 'line',
      data: data.map(d => d.gfcri_value),
      smooth: true,
      showSymbol: false,
      lineStyle: { color: COLORS.accent, width: 2 },
      areaStyle: { color: COLORS.accent + '10' },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { type: 'dashed' },
        data: [
          { yAxis: 25, lineStyle: { color: COLORS.green + '60' } },
          { yAxis: 45, lineStyle: { color: COLORS.orange + '60' } },
          { yAxis: 60, lineStyle: { color: COLORS.red + '60' } },
        ],
      },
    }],
  }
})

function formatCurrentValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-'
  const n = Number(value)
  if (!Number.isFinite(n)) return tx(value)
  const abs = Math.abs(n)
  if (abs >= 1000) return Math.round(n).toLocaleString()
  if (abs >= 100) return n.toFixed(1)
  if (abs >= 10) return n.toFixed(2)
  return n.toFixed(3)
}

function hiddenStatusFromBoost(boost: number): string {
  if (boost >= 15) return 'critical'
  if (boost >= 8) return 'significant'
  if (boost > 0) return 'mild'
  return 'none'
}

function hiddenRiskStatusLabel(status: string): string {
  if (status === 'critical') return t('dash.hiddenCritical')
  if (status === 'significant') return t('dash.hiddenSignificant')
  if (status === 'mild') return t('dash.hiddenMild')
  return t('dash.hiddenNoneStatus')
}

function hiddenDetailText(detail: any): string {
  if (!detail) return t('analysis.hiddenNone')
  if (detail.detail) return tx(detail.detail)
  if (detail.type === 'policy_mask') return t('dash.hiddenPolicyMask')
  if (detail.type === 'zscore_desensitized') return t('dash.hiddenDesensitized')
  if (detail.type === 'surface_calm_deep_stress') return t('dash.hiddenSurfaceCalm')
  return tx(detail.title || detail.type || t('analysis.hiddenRisk'))
}

</script>

<style scoped>
/* ── Root ── */
.dashboard-root {
  position: relative;
  isolation: isolate;
}

.terminal-subtitle {
  color: var(--text);
  font-size: 16px;
  font-weight: 400;
  margin-top: 4px;
}

.section-head {
  align-items: start;
  display: flex;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 10px;
}

.command-center {
  margin-bottom: 28px;
  padding: 22px;
}

.command-topbar {
  align-items: start;
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(360px, 0.9fr);
  gap: 24px;
}

.command-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.command-meta-cell {
  background: rgba(255,255,255,0.016);
  border: 1px solid var(--border);
  border-radius: 8px;
  min-height: 70px;
  padding: 12px;
}

.command-meta-cell span {
  color: var(--muted);
  display: block;
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.command-meta-cell strong {
  color: var(--text);
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 15px;
  font-weight: 500;
  margin-top: 8px;
}

.command-grid {
  display: grid;
  grid-template-columns: minmax(250px, 0.78fr) minmax(440px, 1.34fr) minmax(310px, 0.9fr);
  gap: 16px;
  margin-top: 22px;
  align-items: stretch;
}

.score-console,
.decision-console,
.trend-panel {
  background: rgba(255,255,255,0.018);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}

.score-console {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.score-console-head,
.console-head,
.board-head {
  align-items: start;
  display: flex;
  gap: 14px;
  justify-content: space-between;
}

.risk-score-row {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin: 8px 0 10px;
}

.risk-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 46px;
  font-weight: 500;
  line-height: 1;
}

.score-delta {
  border: 1px solid var(--border);
  border-radius: 999px;
  flex: 0 0 auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  padding: 5px 8px;
}

.score-delta-up {
  color: var(--orange);
}

.score-delta-down {
  color: var(--green);
}

.risk-alert {
  border: 1px solid;
  border-radius: 999px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.08em;
  padding: 4px 8px;
  text-transform: uppercase;
}

.score-summary {
  min-height: 64px;
}

.regime-stack {
  border: 1px solid var(--border);
  border-radius: 10px;
  display: grid;
  gap: 0;
  margin-top: 18px;
  overflow: hidden;
}

.regime-line {
  align-items: center;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 12px;
}

.regime-line:last-child {
  border-bottom: 0;
}

.regime-line span,
.evidence-cell span,
.queue-item span {
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.regime-line strong,
.evidence-cell strong,
.queue-item strong {
  color: var(--text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 500;
  text-align: right;
}

.score-actions {
  display: grid;
  gap: 8px;
  grid-template-columns: 1fr 1fr;
  margin-top: auto;
  padding-top: 18px;
}

.score-actions a {
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--accent);
  font-size: 11px;
  padding: 8px 10px;
  text-align: center;
}

.score-actions a:hover,
.receipt-link:hover {
  border-color: rgba(129,140,248,0.45);
  color: var(--text);
}

.judgment-band {
  background: linear-gradient(90deg, rgba(129,140,248,0.10), rgba(255,255,255,0.014));
  border: 1px solid rgba(129,140,248,0.18);
  border-radius: 10px;
  margin-top: 14px;
  padding: 14px;
}

.judgment-status {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.judgment-band p {
  color: var(--text);
  font-size: 14px;
  line-height: 1.55;
  margin-top: 6px;
}

.evidence-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  margin-top: 14px;
}

.evidence-cell {
  background: rgba(255,255,255,0.014);
  border: 1px solid var(--border);
  border-radius: 8px;
  min-height: 72px;
  padding: 10px;
}

.evidence-cell strong {
  display: block;
  font-size: 18px;
  margin-top: 8px;
  text-align: left;
}

.console-split {
  display: grid;
  gap: 14px;
  grid-template-columns: minmax(0, 1.2fr) minmax(230px, 0.8fr);
  margin-top: 14px;
}

.driver-board,
.risk-queue {
  border: 1px solid var(--border);
  border-radius: 10px;
  min-width: 0;
  padding: 12px;
}

.board-head span {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.45;
  text-align: right;
}

.driver-table {
  display: grid;
  gap: 0;
  margin-top: 10px;
}

.driver-table-row {
  align-items: center;
  border-top: 1px solid var(--border);
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(0, 1.35fr) 0.72fr 0.62fr 0.62fr;
  min-height: 34px;
}

.driver-table-row span {
  color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  min-width: 0;
}

.driver-table-head {
  border-top: 0;
}

.driver-table-head span {
  color: color-mix(in srgb, var(--muted) 70%, transparent);
  font-size: 9px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.driver-label {
  color: var(--text) !important;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.risk-queue {
  display: grid;
  gap: 10px;
}

.queue-item {
  border-left: 2px solid rgba(129,140,248,0.34);
  padding-left: 10px;
}

.queue-next {
  border-left-color: rgba(249,115,22,0.58);
}

.queue-item strong {
  display: block;
  margin-top: 4px;
  text-align: left;
}

.queue-item p {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.52;
  margin-top: 4px;
}

.command-right-rail {
  min-width: 0;
}

.compact-receipt {
  margin-top: 16px;
}

.model-lens-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  margin-top: 16px;
}

.score-receipt {
  background: rgba(255,255,255,0.014);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}

.receipt-head {
  align-items: start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
}

.receipt-link {
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--accent);
  flex: 0 0 auto;
  font-size: 11px;
  padding: 6px 10px;
}

.receipt-grid {
  align-items: center;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 10px;
  margin-top: 14px;
}

.receipt-step {
  background: rgba(255,255,255,0.018);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
}

.receipt-step span {
  color: var(--muted);
  display: block;
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.receipt-step strong {
  color: var(--text);
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 500;
  margin-top: 4px;
}

.receipt-final {
  border-color: rgba(129,140,248,0.28);
}

.receipt-op {
  color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  text-align: center;
}

/* ── Noise overlay ── */
.noise-overlay {
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 9999;
  opacity: 0.012;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-size: 128px 128px;
  mix-blend-mode: overlay;
}

/* ── Signal Cards ── */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.signal-card {
  position: relative;
  overflow: hidden;
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 2px solid var(--card-accent);
  border-radius: 10px;
  padding: 24px;
  transition: border-color 0.35s ease, box-shadow 0.35s ease, transform 0.35s ease;
  cursor: default;
}

.signal-card:hover {
  border-color: color-mix(in srgb, var(--card-accent) 40%, var(--border));
  box-shadow: 0 10px 28px rgba(0,0,0,0.18);
  transform: translateY(-2px);
}

/* Gradient overlay that shifts on hover */
.card-gradient {
  pointer-events: none;
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--card-accent) 6%, transparent) 0%,
    transparent 60%
  );
  opacity: 0;
  transition: opacity 0.35s ease;
  border-radius: 12px;
}

.signal-card:hover .card-gradient {
  opacity: 1;
}

.card-label {
  font-size: 9px;
  letter-spacing: 3.5px;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 12px;
  font-family: 'JetBrains Mono', monospace;
}

.card-value {
  font-size: 40px;
  font-weight: 200;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1;
  margin-bottom: 12px;
}

.card-detail {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

/* ── Chart Section ── */
.chart-section {
  margin-bottom: 48px;
}

.section-header {
  margin-bottom: 20px;
}

.section-eyebrow {
  font-size: 10px;
  letter-spacing: 5px;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 4px;
  font-family: 'JetBrains Mono', monospace;
}

.section-title {
  font-size: 17px;
  font-weight: 300;
  color: white;
}

.chart-container {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: var(--card);
  border: 1px solid var(--border);
}

/* Dot grid background mimicking radar screen */
.chart-grid-bg {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
  z-index: 0;
}

/* Scan-line animation — a thin bright strip sweeping top-to-bottom */
.scanline-overlay {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(129, 140, 248, 0.15) 40%,
    rgba(129, 140, 248, 0.35) 50%,
    rgba(129, 140, 248, 0.15) 60%,
    transparent 100%
  );
  animation: scanline 4s linear infinite;
  pointer-events: none;
  z-index: 2;
}

@keyframes scanline {
  0%   { top: 0%;   opacity: 0; }
  5%   { opacity: 1; }
  95%  { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* ── Trust Bar ── */
.trust-bar {
  text-align: center;
  padding: 28px 0 36px;
}

.trust-separator {
  height: 1px;
  margin-bottom: 32px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(129,140,248,0.12) 20%,
    rgba(129,140,248,0.25) 50%,
    rgba(129,140,248,0.12) 80%,
    transparent 100%
  );
}

@keyframes sep-shimmer {
  0%, 100% { opacity: 0.6; }
  50%       { opacity: 1; }
}

.trust-powered {
  font-size: 9px;
  letter-spacing: 4px;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--muted) 35%, transparent);
  margin-bottom: 10px;
  font-family: 'JetBrains Mono', monospace;
}

.trust-sources {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
}

.trust-item {
  font-size: 11px;
  color: color-mix(in srgb, var(--muted) 30%, transparent);
  font-family: 'JetBrains Mono', monospace;
  transition: color 0.3s ease;
  cursor: default;
}

.trust-item:hover {
  color: color-mix(in srgb, var(--muted) 70%, transparent);
}

.trust-note {
  color: color-mix(in srgb, var(--muted) 70%, transparent);
  font-size: 11px;
  line-height: 1.6;
  max-width: 720px;
  margin: 14px auto 0;
}

.trust-dot {
  font-size: 11px;
  color: color-mix(in srgb, var(--muted) 20%, transparent);
}

/* ── Empty state ── */
.empty-state {
  color: var(--muted);
  text-align: center;
  padding: 80px 0;
  font-size: 14px;
}

/* ── Scroll-triggered fade-in (staggered) ── */
.fade-in {
  animation: fadeUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
  opacity: 0;
  transform: translateY(28px);
}

.fade-in-delay-1 { animation-delay: 0.12s; }
.fade-in-delay-2 { animation-delay: 0.22s; }
.fade-in-delay-3 { animation-delay: 0.32s; }

@keyframes fadeUp {
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 1280px) {
  .command-grid {
    grid-template-columns: minmax(250px, 0.8fr) minmax(0, 1.2fr);
  }

  .command-right-rail {
    grid-column: 1 / -1;
  }

  .command-right-rail {
    display: grid;
    gap: 16px;
    grid-template-columns: minmax(0, 1fr) minmax(300px, 0.8fr);
  }

  .command-right-rail .mt-4 {
    margin-top: 0;
  }
}

@media (max-width: 960px) {
  .command-topbar,
  .command-grid,
  .console-split,
  .command-right-rail,
  .model-lens-grid {
    grid-template-columns: 1fr;
  }

  .command-meta,
  .cards-grid,
  .receipt-grid,
  .evidence-grid {
    grid-template-columns: 1fr;
  }

  .command-center {
    padding: 16px;
  }

  .score-console-head,
  .console-head,
  .board-head,
  .receipt-head {
    flex-direction: column;
  }

  .score-actions {
    grid-template-columns: 1fr;
  }

  .receipt-op {
    display: none;
  }
}
</style>
