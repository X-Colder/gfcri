<template>
  <div class="space-y-6">
    <section class="terminal-section fade-in">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p class="terminal-kicker">{{ t('institutional.radarKicker') }}</p>
          <h1 class="terminal-title">{{ t('institutional.radarTitle') }}</h1>
          <p class="terminal-copy mt-2 max-w-3xl">{{ t('institutional.radarSubtitle') }}</p>
        </div>
        <div class="grid gap-3 sm:grid-cols-[1fr_auto] xl:min-w-[460px]">
          <div class="grid grid-cols-3 gap-2">
            <div class="terminal-metric">
              <span>{{ t('institutional.sources') }}</span>
              <strong>{{ radar?.source_count ?? '-' }}</strong>
            </div>
            <div class="terminal-metric">
              <span>{{ t('institutional.items') }}</span>
              <strong>{{ radar?.item_count ?? '-' }}</strong>
            </div>
            <div class="terminal-metric">
              <span>{{ t('institutional.themes') }}</span>
              <strong>{{ radar?.theme_summary.length ?? '-' }}</strong>
            </div>
          </div>
          <button
            class="rounded-lg border border-[var(--border)] px-4 py-2 text-xs font-medium text-white transition hover:border-[var(--accent)] hover:text-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="loading || refreshing"
            @click="loadRadar(true)"
          >
            {{ refreshing ? t('common.loading') : t('institutional.refresh') }}
          </button>
        </div>
      </div>
    </section>

    <section class="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.8fr)]">
      <div class="terminal-section p-5">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p class="terminal-kicker">{{ t('institutional.signals') }}</p>
            <h2 class="mt-1 text-base font-medium text-white">{{ t('institutional.watchImpact') }}</h2>
          </div>
          <p class="text-[11px] text-[var(--muted)]">{{ t('institutional.updated') }}: {{ formatDate(radar?.generated_at) }}</p>
        </div>

        <div v-if="loading" class="mt-5 rounded-lg border border-[var(--border)] bg-white/[0.012] p-5 text-sm text-[var(--muted)]">
          {{ t('common.loading') }}
        </div>
        <div v-else-if="error && !radar" class="mt-5 rounded-lg border border-red-500/30 bg-red-500/10 p-5 text-sm text-red-100">
          {{ t('institutional.loadError') }}
        </div>
        <div v-else-if="topItems.length === 0" class="mt-5 rounded-lg border border-[var(--border)] bg-white/[0.012] p-5 text-sm text-[var(--muted)]">
          {{ t('institutional.emptyRadar') }}
        </div>

        <div v-else class="mt-5 space-y-3">
          <article
            v-for="item in topItems"
            :key="item.id"
            class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-4 transition hover:border-[var(--accent)]/50"
          >
            <div class="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2 text-[11px] text-[var(--muted)]">
                  <span class="rounded border border-[var(--border)] px-2 py-0.5 text-white">{{ item.source }}</span>
                  <span>{{ t('institutional.sourceTier') }} {{ item.source_tier }}</span>
                  <span>{{ formatDate(item.published_at) }}</span>
                </div>
                <a
                  class="mt-2 block text-sm font-medium leading-snug text-white hover:text-[var(--accent)]"
                  :href="item.url"
                  target="_blank"
                  rel="noreferrer"
                >
                  {{ item.title }}
                </a>
              </div>
              <div class="flex shrink-0 items-center gap-2 text-[11px]">
                <span class="rounded bg-[var(--accent)]/10 px-2 py-1 text-[var(--accent)]">{{ directionLabel(item.risk_direction) }}</span>
                <span class="rounded border border-[var(--border)] px-2 py-1 text-[var(--muted)]">{{ Math.round(item.confidence * 100) }}%</span>
              </div>
            </div>

            <p v-if="item.summary" class="mt-3 line-clamp-2 text-xs leading-relaxed text-[var(--muted)]">{{ item.summary }}</p>

            <div class="mt-4 grid gap-3 lg:grid-cols-3">
              <div>
                <p class="text-[10px] uppercase tracking-wide text-[var(--muted)]">{{ t('institutional.themes') }}</p>
                <div class="mt-2 flex flex-wrap gap-1.5">
                  <span v-for="theme in item.risk_themes" :key="theme" class="rounded bg-white/[0.04] px-2 py-1 text-[11px] text-white">
                    {{ themeLabel(theme) }}
                  </span>
                </div>
              </div>
              <div>
                <p class="text-[10px] uppercase tracking-wide text-[var(--muted)]">{{ t('institutional.mappedNodes') }}</p>
                <p class="mt-2 text-xs leading-relaxed text-white">{{ compactList(item.affected_nodes.map(nodeLabel), 4) }}</p>
              </div>
              <div>
                <p class="text-[10px] uppercase tracking-wide text-[var(--muted)]">{{ t('institutional.mappedChains') }}</p>
                <p class="mt-2 text-xs leading-relaxed text-white">{{ compactList(item.affected_chains.map(chainLabel), 3) }}</p>
              </div>
            </div>
          </article>
        </div>
      </div>

      <aside class="space-y-5">
        <div class="terminal-section p-5">
          <p class="terminal-kicker">{{ t('institutional.themeMap') }}</p>
          <div class="mt-4 space-y-3">
            <div v-for="theme in topThemes" :key="theme.theme" class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-3">
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-medium text-white">{{ themeLabel(theme.theme) }}</p>
                <span class="rounded bg-white/[0.05] px-2 py-1 text-xs text-[var(--muted)]">{{ theme.count }}</span>
              </div>
              <p class="mt-2 text-[11px] leading-relaxed text-[var(--muted)]">{{ theme.sources.join(' / ') }}</p>
              <p class="mt-2 text-xs leading-relaxed text-white">{{ compactList(theme.affected_nodes.map(nodeLabel), 5) }}</p>
            </div>
          </div>
        </div>

        <div class="terminal-section p-5">
          <p class="terminal-kicker">{{ t('institutional.methodology') }}</p>
          <p class="mt-3 text-xs leading-relaxed text-[var(--muted)]">{{ t('institutional.watchImpactBody') }}</p>
          <p class="mt-3 text-xs leading-relaxed text-[var(--muted)]">{{ t('institutional.officialOnly') }}</p>
          <div v-if="radar?.errors.length" class="mt-4 rounded-lg border border-amber-400/30 bg-amber-400/10 p-3">
            <p class="text-xs font-medium text-amber-100">{{ t('institutional.partialError') }}</p>
            <p class="mt-1 text-[11px] text-amber-100/70">{{ errorSources }}</p>
          </div>
        </div>
      </aside>
    </section>

    <section class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.9fr)]">
      <div class="terminal-section p-5">
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
        <div class="terminal-section p-5">
          <p class="terminal-kicker">{{ t('institutional.package') }}</p>
          <div class="mt-4 space-y-3">
            <div v-for="item in packageItems" :key="item" class="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-white/[0.012] px-3 py-2">
              <span class="h-1.5 w-1.5 rounded-full bg-[var(--accent)]"></span>
              <span class="text-xs text-white">{{ item }}</span>
            </div>
          </div>
        </div>

        <div class="terminal-section p-5">
          <p class="terminal-kicker">{{ t('institutional.positioning') }}</p>
          <p class="mt-3 text-xs leading-relaxed text-[var(--muted)]">{{ t('institutional.positioningBody') }}</p>
        </div>
      </div>
    </section>

    <CrisisRegimePanel />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from '@/composables/useI18n'
import { fetchInstitutionalRadar } from '@/api/institutionalRadar'
import type { InstitutionalRadar } from '@/api/types'
import CrisisRegimePanel from '@/components/common/CrisisRegimePanel.vue'

const { t, lang } = useI18n()

const radar = ref<InstitutionalRadar | null>(null)
const loading = ref(true)
const refreshing = ref(false)
const error = ref('')

const themeLabels: Record<string, { zh: string; en: string }> = {
  'AI Capex / Tech Bubble': { zh: 'AI 资本开支 / 科技泡沫', en: 'AI Capex / Tech Bubble' },
  'Dollar Liquidity': { zh: '美元流动性', en: 'Dollar Liquidity' },
  'Global Credit': { zh: '全球信用', en: 'Global Credit' },
  'Bank Funding': { zh: '银行融资', en: 'Bank Funding' },
  'Europe Sovereign / Credit': { zh: '欧洲主权 / 信用', en: 'Europe Sovereign / Credit' },
  'China Credit': { zh: '中国信用', en: 'China Credit' },
  'Commodity / Energy Shock': { zh: '商品 / 能源冲击', en: 'Commodity / Energy Shock' },
  'Japan Carry / Yen': { zh: '日本套息 / 日元', en: 'Japan Carry / Yen' },
  'EM Debt / FX': { zh: '新兴市场债务 / 汇率', en: 'EM Debt / FX' },
  'General Macro / Policy': { zh: t('institutional.generalMacro'), en: t('institutional.generalMacro') },
}

const nodeLabels: Record<string, { zh: string; en: string }> = {
  ai_capex: { zh: 'AI/云资本开支篮子', en: 'AI/Cloud Capex Basket' },
  orcl_cds: { zh: 'AI/云信用压力代理', en: 'AI/Cloud Credit Stress Proxy' },
  sox: { zh: '半导体指数', en: 'Semiconductor Index' },
  dram_spot: { zh: 'DRAM 生产商篮子', en: 'DRAM Producer Basket' },
  nand_spot: { zh: 'NAND/存储生产商篮子', en: 'NAND/Storage Producer Basket' },
  dxy: { zh: '美元指数', en: 'DXY Index' },
  global_liqd: { zh: '美联储资产负债表', en: 'Fed Balance Sheet' },
  fred_sofr: { zh: 'SOFR', en: 'SOFR' },
  sofr_effr_spread: { zh: 'SOFR-EFFR 利差', en: 'SOFR-EFFR Spread' },
  ust_10y: { zh: '美国10年期国债收益率', en: 'US 10Y Treasury Yield' },
  fred_hy_spread: { zh: '美国高收益信用利差', en: 'US High Yield Spread' },
  fred_bbb_spread: { zh: '美国 BBB 信用利差', en: 'US BBB Spread' },
  fred_baa10y_spread: { zh: 'BAA-10Y 信用利差', en: 'BAA-10Y Credit Spread' },
  fred_euro_hy_spread: { zh: '欧洲高收益信用利差', en: 'Euro HY Spread' },
  fred_all_loan_delinquency: { zh: '美国贷款逾期率', en: 'US Loan Delinquency Rate' },
  kre: { zh: '美国区域银行', en: 'US Regional Banks' },
  cny_usd: { zh: '人民币兑美元', en: 'CNY/USD' },
  hsi: { zh: '恒生指数', en: 'Hang Seng Index' },
  eurusd: { zh: '欧元兑美元', en: 'EUR/USD' },
  oil_wti: { zh: 'WTI 原油', en: 'WTI Crude Oil' },
  gold: { zh: '黄金', en: 'Gold' },
  jpy_usd: { zh: '日元兑美元', en: 'JPY/USD' },
  nikkei: { zh: '日经指数', en: 'Nikkei' },
  vix: { zh: 'VIX 波动率', en: 'VIX' },
  emb: { zh: '新兴市场债券', en: 'EM Bonds' },
  eem: { zh: '新兴市场股票', en: 'EM Equities' },
}

const chainLabels: Record<string, { zh: string; en: string }> = {
  ai_semi_cycle: { zh: 'AI/半导体周期', en: 'AI/Semiconductor Cycle' },
  fed_cascade: { zh: '美联储政策传导', en: 'Fed Policy Cascade' },
  dollar_squeeze: { zh: '美元挤压', en: 'Dollar Squeeze' },
  credit_contagion: { zh: '信用传染', en: 'Credit Contagion' },
  housing_bank_doom: { zh: '住房-银行压力链', en: 'Housing-Bank Stress Chain' },
  europe_contagion: { zh: '欧洲传染', en: 'Europe Contagion' },
  china_shockwave: { zh: '中国冲击波', en: 'China Shockwave' },
  food_energy_shock: { zh: '食品能源冲击', en: 'Food/Energy Shock' },
  safe_haven_flight: { zh: '避险资金流', en: 'Safe-Haven Flight' },
  yen_carry_unwind: { zh: '日元套息平仓', en: 'Yen Carry Unwind' },
  crypto_contagion: { zh: '加密资产传染', en: 'Crypto Contagion' },
}

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

const topItems = computed(() => radar.value?.items.slice(0, 10) ?? [])
const topThemes = computed(() => radar.value?.theme_summary.slice(0, 6) ?? [])
const errorSources = computed(() => radar.value?.errors.map((item) => item.source).join(', ') ?? '')

async function loadRadar(refresh = false) {
  error.value = ''
  if (refresh) refreshing.value = true
  else loading.value = true
  try {
    radar.value = await fetchInstitutionalRadar(30, refresh)
  } catch (err: any) {
    error.value = err?.message || 'load failed'
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function formatDate(value?: string | null): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(lang.value === 'zh' ? 'zh-CN' : 'en-US', {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function localized(map?: { zh: string; en: string }, fallback = '-'): string {
  if (!map) return fallback
  return lang.value === 'zh' ? map.zh : map.en
}

function themeLabel(theme: string): string {
  return localized(themeLabels[theme], theme)
}

function nodeLabel(node: string): string {
  return localized(nodeLabels[node], node.replace(/_/g, ' '))
}

function chainLabel(chain: string): string {
  return localized(chainLabels[chain], chain.replace(/_/g, ' '))
}

function directionLabel(direction: string): string {
  if (direction === 'pressure_up') return t('institutional.pressureUp')
  return t('institutional.monitoring')
}

function compactList(values: string[], limit: number): string {
  if (!values.length) return '-'
  const visible = values.slice(0, limit)
  const extra = values.length - visible.length
  return extra > 0 ? `${visible.join(', ')} +${extra}` : visible.join(', ')
}

onMounted(() => loadRadar(false))
</script>
