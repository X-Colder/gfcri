<template>
  <section v-if="hasTrade" class="trade-panel bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 lg:p-5 card-hover">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="min-w-0">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[3px]">{{ t('trade.kicker') }}</p>
        <h3 class="mt-1 text-sm font-medium text-white">{{ t('trade.title') }}</h3>
        <p class="terminal-copy mt-2">{{ t('trade.desc') }}</p>
      </div>
      <div class="grid grid-cols-2 gap-2 sm:min-w-[260px]">
        <div class="terminal-metric">
          <span>{{ t('trade.score') }}</span>
          <strong :style="{ color: scoreColor(score) }">{{ score.toFixed(1) }}</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ t('trade.boost') }}</span>
          <strong :style="{ color: boost > 0 ? 'var(--orange)' : 'var(--muted)' }">+{{ boost.toFixed(1) }}</strong>
        </div>
      </div>
    </div>

    <div class="mt-4 grid gap-3" :class="compact ? 'lg:grid-cols-2' : 'xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]'">
      <div class="rounded-lg border border-[var(--border)] bg-white/[0.012] overflow-hidden">
        <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <p class="text-xs font-medium text-white">{{ t('trade.topLinks') }}</p>
          <span class="font-mono text-[10px] text-[var(--muted)]">{{ dataVersion }}</span>
        </div>
        <div class="divide-y divide-[var(--border)]/50">
          <div v-for="link in visibleLinks" :key="`${link.source}-${link.target}-${link.sector}`" class="px-4 py-3">
            <div class="flex items-center gap-2">
              <span class="truncate text-xs text-white">{{ economyName(link.source_name || link.source) }}</span>
              <span class="font-mono text-[10px] text-[var(--muted)]">-></span>
              <span class="truncate text-xs text-white">{{ economyName(link.target_name || link.target) }}</span>
              <span class="ml-auto shrink-0 font-mono text-xs" :style="{ color: scoreColor(Number(link.spillover || 0)) }">
                {{ Number(link.spillover || 0).toFixed(1) }}
              </span>
            </div>
            <p class="mt-1 text-[11px] leading-relaxed text-[var(--muted)]">{{ linkDetail(link) }}</p>
            <div v-if="!compact" class="mt-2 flex flex-wrap gap-1.5">
              <span v-for="node in link.affected_nodes || []" :key="node" class="rounded border border-[var(--border)] px-2 py-0.5 font-mono text-[10px] text-[var(--muted)]">
                {{ nodeLabel(node) }}
              </span>
            </div>
          </div>
          <p v-if="!visibleLinks.length" class="px-4 py-3 text-xs text-[var(--muted)]">{{ t('trade.empty') }}</p>
        </div>
      </div>

      <div class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
        <div class="mb-3 flex items-center justify-between">
          <p class="text-xs font-medium text-white">{{ t('trade.exposures') }}</p>
          <span class="text-[10px] text-[var(--muted)]">{{ t('trade.additive') }}</span>
        </div>
        <div class="space-y-3">
          <div v-for="item in visibleExposures" :key="item.economy" class="grid grid-cols-[minmax(0,90px)_1fr_auto] items-center gap-2">
            <span class="truncate text-xs text-[var(--muted)]">{{ economyName(item.economy_name || item.economy) }}</span>
            <div class="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
              <div class="h-full rounded-full" :style="{ width: Math.min(Number(item.score || 0), 100) + '%', backgroundColor: scoreColor(Number(item.score || 0)) }"></div>
            </div>
            <span class="w-10 text-right font-mono text-[10px] text-white">{{ Number(item.score || 0).toFixed(1) }}</span>
          </div>
        </div>
        <p v-if="!compact" class="mt-4 text-[11px] leading-relaxed text-[var(--muted)]">{{ t('trade.staticNote') }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { COLORS } from '@/composables/useTheme'
import { useI18n } from '@/composables/useI18n'
import { useRiskStore } from '@/stores/risk'

defineProps<{ compact?: boolean }>()

const riskStore = useRiskStore()
const { t, tx, lang } = useI18n()

const trade = computed(() => {
  const latest = riskStore.latest
  const subTrade = latest?.sub_index_details?.SI_TRADE_SPILLOVER
  return latest?.trade_spillover || subTrade?.trade_spillover || null
})

const boost = computed(() => {
  const latest = riskStore.latest
  const subTrade = latest?.sub_index_details?.SI_TRADE_SPILLOVER
  return Number(latest?.trade_spillover_boost ?? subTrade?.trade_spillover_boost ?? 0)
})

const score = computed(() => Number(trade.value?.score || 0))
const dataVersion = computed(() => String(trade.value?.data_version || 'static-v1'))
const topLinks = computed(() => Array.isArray(trade.value?.top_links) ? trade.value.top_links : [])
const exposures = computed(() => Array.isArray(trade.value?.economy_exposures) ? trade.value.economy_exposures : [])
const visibleLinks = computed(() => topLinks.value.slice(0, 4))
const visibleExposures = computed(() => exposures.value.slice(0, 5))
const hasTrade = computed(() => !!trade.value && (score.value > 0 || topLinks.value.length > 0))

const economyZh: Record<string, string> = {
  'United States': '美国',
  China: '中国',
  Eurozone: '欧元区',
  Japan: '日本',
  'South Korea': '韩国',
  Taiwan: '中国台湾',
  Germany: '德国',
  'United Kingdom': '英国',
  India: '印度',
  Brazil: '巴西',
  Australia: '澳大利亚',
  Canada: '加拿大',
  Mexico: '墨西哥',
  Singapore: '新加坡',
  'Global Commodities': '全球商品',
  'Emerging Markets': '新兴市场',
}

const sectorZh: Record<string, string> = {
  semiconductors: '半导体',
  'capital goods': '资本品',
  'industrial exports': '工业出口',
  'bulk commodities': '大宗商品',
  'consumer demand': '消费需求',
  'technology demand': '科技需求',
  'manufacturing chain': '制造链',
  'intra-Europe demand': '欧洲内部需求',
  'financial/services trade': '金融与服务贸易',
  'electronics inputs': '电子投入品',
  'electronics cycle': '电子周期',
  'energy imports': '能源进口',
  'commodity beta': '商品敞口',
  'portfolio flows': '组合资金流',
}

function scoreColor(value: number): string {
  if (value >= 50) return COLORS.red
  if (value >= 25) return COLORS.orange
  if (value >= 15) return COLORS.yellow
  return COLORS.green
}

function economyName(name: string): string {
  return lang.value === 'zh' ? (economyZh[name] || tx(name)) : tx(name)
}

function sectorName(sector: string): string {
  return lang.value === 'zh' ? (sectorZh[sector] || sector) : sector
}

function nodeLabel(node: string): string {
  return tx(node)
}

function linkDetail(link: any): string {
  if (lang.value === 'zh') {
    return `${economyName(link.source_name || link.source)} 的${sectorName(link.sector)}压力正在传导至 ${economyName(link.target_name || link.target)}，影响 ${Number(link.spillover || 0).toFixed(1)} 分。`
  }
  return link.description || `${link.source_name || link.source} ${link.sector} stress transmits to ${link.target_name || link.target}.`
}
</script>
