<template>
  <div class="dashboard-root">
    <!-- Noise/grain texture overlay -->
    <div class="noise-overlay" aria-hidden="true"></div>

    <LoadingSpinner v-if="riskStore.loading" />

    <template v-else-if="riskStore.latest">

      <section class="terminal-section dashboard-brief fade-in">
        <div class="brief-header">
          <div>
            <p class="terminal-kicker">{{ t('dash.eyebrow') }}</p>
            <h1 class="terminal-title">{{ t('dash.title') }}</h1>
            <p class="terminal-copy mt-2">{{ t('dash.subtitle') }}</p>
          </div>
          <div class="brief-meta">
            <div class="terminal-metric">
              <span>{{ t('dash.latestObservation') }}</span>
              <strong>{{ riskStore.latest.index_date }}</strong>
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
        </div>

        <div class="brief-grid">
          <div class="risk-score-panel">
            <p class="terminal-kicker">GFCRI</p>
            <div class="risk-score-row">
              <span class="risk-score" :style="{ color: getAlertColor(riskStore.latest.alert_level) }">
                {{ riskStore.latest.gfcri_value.toFixed(1) }}
              </span>
              <span class="risk-alert" :style="{ color: getAlertColor(riskStore.latest.alert_level), borderColor: getAlertColor(riskStore.latest.alert_level) }">
                {{ t('alert.' + riskStore.latest.alert_level) }}
              </span>
            </div>
            <p class="terminal-copy">{{ heroSummary }}</p>
          </div>

          <div class="driver-panel">
            <p class="terminal-kicker">{{ t('dash.primaryDriver') }}</p>
            <p class="driver-name">{{ primaryDriver }}</p>
            <p class="terminal-copy mt-2">{{ t('dash.methodologyShort') }}</p>
          </div>
        </div>
      </section>

      <!-- ── Hero Section ── -->
      <div class="hero-section fade-in fade-in-delay-1" ref="heroRef">

        <!-- Eyebrow label -->
        <p class="eyebrow">{{ t('dash.eyebrow') }}</p>

        <!-- Score ring + number -->
        <div class="score-ring-wrapper">
          <svg class="score-ring" viewBox="0 0 220 220" fill="none" aria-hidden="true">
            <!-- Track -->
            <circle
              cx="110" cy="110" r="96"
              stroke="rgba(255,255,255,0.05)"
              stroke-width="3"
              stroke-linecap="round"
            />
            <!-- Progress arc -->
            <circle
              cx="110" cy="110" r="96"
              :stroke="getAlertColor(riskStore.latest.alert_level)"
              stroke-width="3"
              stroke-linecap="round"
              stroke-dasharray="603.186"
              :stroke-dashoffset="ringOffset"
              transform="rotate(-90 110 110)"
              class="ring-arc"
            />
            <!-- Tick marks at 25/50/75 -->
            <line v-for="tick in ringTicks" :key="tick.angle"
              :x1="tick.x1" :y1="tick.y1" :x2="tick.x2" :y2="tick.y2"
              stroke="rgba(255,255,255,0.15)" stroke-width="1"
            />
          </svg>

          <!-- Glow halo behind the number -->
          <div
            class="score-glow"
            :style="{ '--glow-color': getAlertColor(riskStore.latest.alert_level) }"
          ></div>

          <!-- The big number -->
          <p
            class="score-number"
            :style="{ color: getAlertColor(riskStore.latest.alert_level) }"
          >{{ riskStore.latest.gfcri_value.toFixed(1) }}</p>
        </div>

        <!-- Alert badge with pulsing dot -->
        <div class="alert-badge">
          <span
            class="alert-dot"
            :style="{ '--dot-color': getAlertColor(riskStore.latest.alert_level) }"
          ></span>
          <span
            class="alert-label"
            :style="{ color: getAlertColor(riskStore.latest.alert_level) }"
          >{{ t('alert.' + riskStore.latest.alert_level) }}</span>
        </div>

        <!-- AI summary -->
        <p class="hero-summary">{{ heroSummary }}</p>
        <p class="hero-date">{{ riskStore.latest.index_date }}</p>
      </div>

      <!-- ── Signal Cards ── -->
      <Paywall :blurred="!isPro" :title="t('dash.anomalous')" :description="t('common.upgradeDesc')">
      <div class="cards-grid fade-in fade-in-delay-2">

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
      <div class="fade-in fade-in-delay-3" style="margin-bottom: 32px;">
        <GlobeNetwork />
      </div>

      <!-- ── Trust Bar ── -->
      <div class="trust-bar fade-in fade-in-delay-3">
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
import { computed, onMounted, ref } from 'vue'

import { useRiskStore } from '@/stores/risk'
import { COLORS, getAlertColor } from '@/composables/useTheme'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Paywall from '@/components/common/Paywall.vue'
import GlobeNetwork from '@/components/charts/GlobeNetwork.vue'

const riskStore = useRiskStore()
const { isPro } = useAuth()
const { t, tx } = useI18n()
const heroRef = ref<HTMLElement | null>(null)

onMounted(() => {
  riskStore.loadLatest()
})

// Circular progress ring: circumference = 2π × 96 ≈ 603.186
const ringOffset = computed(() => {
  const val = riskStore.latest?.gfcri_value ?? 0
  const pct = Math.min(Math.max(val / 100, 0), 1)
  return 603.186 * (1 - pct)
})

// Tick marks at 0°, 90°, 180° (0, 25, 50, 75 of the scale)
const ringTicks = computed(() => {
  const cx = 110, cy = 110, r = 96, tickLen = 8
  return [0, 90, 180, 270].map(deg => {
    const rad = (deg - 90) * (Math.PI / 180)
    const cos = Math.cos(rad), sin = Math.sin(rad)
    return {
      angle: deg,
      x1: cx + (r - tickLen) * cos,
      y1: cy + (r - tickLen) * sin,
      x2: cx + r * cos,
      y2: cy + r * sin,
    }
  })
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
    .sort((a: any, b: any) => Math.abs(b[1].zscore || 0) - Math.abs(a[1].zscore || 0))[0]
  if (!item) return t('dash.noDriver')
  return tx((item[1] as any).display_name || item[0])
})

const heroSummary = computed(() => {
  const ac = activeChainCount.value
  const an = anomalyCount.value
  if (an > 8 && ac >= 5) return t('dash.summary.high', { an, ac })
  if (ac >= 5) return t('dash.summary.chains', { ac })
  if (an > 5) return t('dash.summary.anomaly', { an })
  return t('dash.summary.normal')
})

</script>

<style scoped>
/* ── Root ── */
.dashboard-root {
  position: relative;
  isolation: isolate;
}

.dashboard-brief {
  margin-bottom: 24px;
}

.brief-header {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.9fr);
  gap: 24px;
  align-items: start;
}

.brief-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.brief-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.7fr) minmax(0, 1fr);
  gap: 16px;
  margin-top: 22px;
}

.risk-score-panel,
.driver-panel {
  background: rgba(255,255,255,0.018);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
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

.risk-alert {
  border: 1px solid;
  border-radius: 999px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.08em;
  padding: 4px 8px;
  text-transform: uppercase;
}

.driver-name {
  color: var(--text);
  font-size: 18px;
  font-weight: 500;
  margin-top: 10px;
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

/* ── Hero Section ── */
.hero-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28px 0 32px;
  text-align: center;
}

.eyebrow {
  font-size: 10px;
  letter-spacing: 7px;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 18px;
  font-family: 'JetBrains Mono', monospace;
}

/* Score ring */
.score-ring-wrapper {
  position: relative;
  width: 150px;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.score-ring {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.score-ring circle,
.score-ring line {
  vector-effect: non-scaling-stroke;
}

.ring-arc {
  transition: stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.4s ease;
  filter: drop-shadow(0 0 6px currentColor);
}

.score-glow {
  position: absolute;
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--glow-color) 0%, transparent 70%);
  opacity: 0.06;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.10; transform: scale(0.95); }
  50%       { opacity: 0.20; transform: scale(1.05); }
}

.score-number {
  position: relative;
  font-size: 54px;
  line-height: 1;
  font-weight: 200;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0;
  transition: color 0.4s ease;
  text-shadow: none;
}

/* Alert badge */
.alert-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.alert-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: var(--dot-color);
  box-shadow: 0 0 6px var(--dot-color);
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1;   box-shadow: 0 0 4px var(--dot-color); }
  50%       { opacity: 0.5; box-shadow: 0 0 12px var(--dot-color); }
}

.alert-label {
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-family: 'JetBrains Mono', monospace;
  transition: color 0.4s ease;
}

.hero-summary {
  font-size: 15px;
  color: var(--muted);
  font-weight: 300;
  line-height: 1.7;
  max-width: 620px;
  margin: 0 auto 12px;
}

.hero-date {
  font-size: 11px;
  color: color-mix(in srgb, var(--muted) 40%, transparent);
  font-family: 'JetBrains Mono', monospace;
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

@media (max-width: 960px) {
  .brief-header,
  .brief-grid {
    grid-template-columns: 1fr;
  }

  .brief-meta,
  .cards-grid {
    grid-template-columns: 1fr;
  }
}
</style>
