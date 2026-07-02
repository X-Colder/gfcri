<template>
  <div>
    <LoadingSpinner v-if="riskStore.loading || reportStore.loading" />

    <template v-else-if="riskStore.latest">

      <!-- Personalized Risk Watch (P2) -->
      <RiskWatch />

      <!-- Section 1: Judgment + Trend -->
      <div class="mb-12 fade-in grid gap-5 xl:grid-cols-[minmax(0,0.88fr)_minmax(420px,1.12fr)]">
        <div v-if="reportStore.latest?.llm_narrative" class="min-w-0">
          <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">AI Analysis</p>
          <h2 class="text-lg font-light text-white mb-6">{{ t("analysis.aiTitle") }}</h2>
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 lg:p-7 card-hover">
            <div v-if="isPro" class="prose prose-invert prose-sm max-w-none judgment-markdown" v-html="renderedNarrative"></div>
            <div v-else>
              <div class="prose prose-invert prose-sm max-w-none judgment-markdown" v-html="truncatedNarrative"></div>
              <div class="relative mt-4">
                <div class="h-20 bg-gradient-to-b from-transparent to-[var(--card)]"></div>
                <div class="text-center -mt-8">
                  <span class="text-xs text-[var(--accent)]">{{ t("analysis.upgradeHint") }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="riskStore.history.length > 1" class="min-w-0">
          <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Historical Trend</p>
          <h2 class="text-lg font-light text-white mb-6">{{ t('analysis.trend') }}</h2>
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 lg:p-5 card-hover">
            <v-chart :option="trendChartOption" style="height: 320px" autoresize />
          </div>
        </div>
      </div>

      <!-- Section 2: Model Logic Breakdown -->
      <div class="mb-12 fade-in fade-in-delay-1">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Model Explainability</p>
        <h2 class="text-lg font-light text-white mb-6">{{ t('analysis.modelLogic') }}</h2>

        <div class="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 lg:p-5 card-hover min-w-0">
            <div class="flex items-center justify-between mb-3">
              <p class="text-sm text-white font-medium">{{ t('analysis.subIndexBreakdown') }}</p>
              <span class="text-[10px] text-[var(--muted)] font-mono">{{ t('dash.coherence') }} {{ (riskStore.latest.coherence_multiplier || 1).toFixed(2) }}x</span>
            </div>
            <v-chart :option="subIndexBreakdownOption" style="height: 320px" autoresize />
          </div>

          <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl overflow-hidden card-hover min-w-0">
            <div class="px-5 py-4 border-b border-[var(--border)] flex items-center justify-between">
              <p class="text-sm text-white font-medium">{{ t('analysis.nodeContribution') }}</p>
              <span class="text-[10px] text-[var(--muted)] font-mono">Top {{ topNodeContributions.length }}</span>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-[var(--muted)] border-b border-[var(--border)]">
                    <th class="text-left px-5 py-2 font-medium">{{ t('analysis.node') }}</th>
                    <th class="text-right px-3 py-2 font-medium">{{ t('analysis.zscore') }}</th>
                    <th class="text-right px-3 py-2 font-medium">{{ t('analysis.absScore') }}</th>
                    <th class="text-right px-5 py-2 font-medium">{{ t('analysis.current') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="node in topNodeContributions" :key="node.id" class="border-b border-[var(--border)]/40 hover:bg-white/[0.02]">
                    <td class="px-5 py-2.5 text-white whitespace-nowrap">{{ node.name }}</td>
                    <td class="px-3 py-2.5 text-right font-mono" :style="{ color: Math.abs(node.zscore) >= 2 ? 'var(--red)' : 'var(--muted)' }">{{ node.zscore.toFixed(2) }}</td>
                    <td class="px-3 py-2.5 text-right font-mono">{{ node.absScoreDisplay }}</td>
                    <td class="px-5 py-2.5 text-right font-mono text-[var(--muted)]">{{ node.currentDisplay }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="mt-5 bg-[var(--card)] border border-[var(--border)] rounded-xl overflow-hidden card-hover">
          <div class="px-5 py-4 border-b border-[var(--border)] flex items-center justify-between">
            <p class="text-sm text-white font-medium">{{ t('analysis.chainPressure') }}</p>
            <span class="text-[10px] text-[var(--muted)] font-mono">{{ activeChains.length }} {{ t('analysis.chainActive') }}</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-xs">
              <thead>
                <tr class="text-[var(--muted)] border-b border-[var(--border)]">
                  <th class="text-left px-5 py-2 font-medium">{{ t('analysis.chain') }}</th>
                  <th class="text-left px-3 py-2 font-medium">{{ t('common.path') }}</th>
                  <th class="text-right px-3 py-2 font-medium">{{ t('analysis.stress') }}</th>
                  <th class="text-right px-5 py-2 font-medium">{{ t('analysis.pathStrength') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="chain in chainPressureRows" :key="chain.id" class="border-b border-[var(--border)]/40 hover:bg-white/[0.02]">
                  <td class="px-5 py-2.5 text-white whitespace-nowrap">{{ chain.name }}</td>
                  <td class="px-3 py-2.5 text-[var(--muted)] min-w-[280px]">{{ chain.path }}</td>
                  <td class="px-3 py-2.5 text-right">
                    <div class="inline-flex items-center gap-2 min-w-[110px] justify-end">
                      <div class="h-1.5 w-16 bg-white/[0.05] rounded-full overflow-hidden">
                        <div class="h-full rounded-full" :style="{ width: Math.min(chain.stress, 100) + '%', backgroundColor: scoreColor(chain.stress) }"></div>
                      </div>
                      <span class="font-mono" :style="{ color: scoreColor(chain.stress) }">{{ chain.stress.toFixed(0) }}</span>
                    </div>
                  </td>
                  <td class="px-5 py-2.5 text-right font-mono text-[var(--muted)]">{{ chain.pathStrength }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Section 2: Transmission Chains — Pro only -->
      <Paywall :blurred="!isPro" :title="t('analysis.unlockChain')" :description="t('analysis.unlockChainDesc')">
      <div class="mb-12 fade-in fade-in-delay-1">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Risk Transmission</p>
        <h2 class="text-lg font-light text-white mb-6">
          {{ t('analysis.chainTitle') }}
          <span class="text-sm text-[var(--muted)] font-normal ml-2">{{ activeChains.length }} {{ t('analysis.chainActive') }} / {{ dormantChains.length }} {{ t('analysis.chainDormant') }}</span>
        </h2>

        <div class="grid gap-4 lg:grid-cols-2">
          <div v-for="chain in sortedChains" :key="chain.id"
               class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 card-hover"
               :class="chain.active ? 'border-l-[3px]' : 'opacity-50'"
               :style="chain.active ? { borderLeftColor: chain.stress >= 50 ? 'var(--red)' : 'var(--orange)' } : {}">
            <div class="flex justify-between items-start mb-2">
              <div>
                <span class="text-xs px-1.5 py-0.5 rounded mr-2"
                      :class="chain.active ? 'bg-[var(--red)]/10 text-[var(--red)]' : 'bg-white/5 text-[var(--muted)]'">
                  {{ chain.active ? t('analysis.transmitting') : t('analysis.sleeping') }}
                </span>
                <span class="text-sm text-white font-medium">{{ tx(chain.name) }}</span>
              </div>
              <span class="text-sm font-mono" :style="{ color: chain.stress >= 50 ? 'var(--red)' : chain.stress >= 30 ? 'var(--orange)' : 'var(--green)' }">
                {{ chain.stress.toFixed(0) }}
              </span>
            </div>
            <p class="text-xs text-[var(--muted)]">{{ chain.path?.map((n: string) => tx(nodeNames[n] || n)).join(' → ') }}</p>
            <div class="mt-3 space-y-1">
              <div v-for="node in chainNodeBars(chain)" :key="node.id" class="flex items-center gap-2">
                <span class="w-24 truncate text-[10px] text-[var(--muted)]">{{ node.name }}</span>
                <div class="h-1.5 flex-1 rounded-full bg-white/[0.05] overflow-hidden">
                  <div class="h-full rounded-full" :style="{ width: node.width + '%', backgroundColor: scoreColor(node.score * 100) }"></div>
                </div>
                <span class="w-8 text-right text-[10px] font-mono text-[var(--muted)]">{{ (node.score * 100).toFixed(0) }}</span>
              </div>
            </div>
            <div class="mt-3 flex items-center justify-between text-[10px] text-[var(--muted)] font-mono">
              <span>{{ t('analysis.pathStrength') }}</span>
              <span>{{ Number(chain.path_strength || 0).toFixed(4) }}</span>
            </div>
          </div>
        </div>
      </div>
      </Paywall>

      <!-- Section 3: Anomalous Indicators — Pro only -->
      <Paywall :blurred="!isPro" :title="t('analysis.unlockAnomaly')" :description="t('analysis.unlockAnomalyDesc')">
      <!-- Section 3: Anomalous Indicators — WHAT is abnormal -->
      <div class="mb-12 fade-in fade-in-delay-2">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Anomaly Detection</p>
        <h2 class="text-lg font-light text-white mb-6">
          {{ t('analysis.anomalyTitle') }}
          <span class="text-sm text-[var(--muted)] font-normal ml-2">{{ anomalousNodes.length }} {{ t('analysis.deviating') }}</span>
        </h2>

        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl overflow-hidden overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-[var(--muted)] text-xs uppercase tracking-wider border-b border-[var(--border)]">
                <th class="text-left px-5 py-3 font-medium">{{ t('analysis.indicator') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.currentVal') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.deviation') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.anomalyScore') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.absScore') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.direction') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="node in anomalousNodes" :key="node.id"
                  class="border-t border-[var(--border)] hover:bg-white/[0.02] transition-colors">
                <td class="px-5 py-3 text-white">{{ tx(node.name) }}</td>
                <td class="px-5 py-3 text-right font-mono text-[var(--muted)]">{{ node.value?.toFixed(2) ?? '—' }}</td>
                <td class="px-5 py-3 text-right font-mono" :style="{ color: Math.abs(node.zscore) > 3 ? 'var(--red)' : 'var(--yellow)' }">
                  {{ Math.abs(node.zscore).toFixed(1) }}×
                </td>
                <td class="px-5 py-3 text-right font-mono text-[var(--muted)]">{{ (node.anomalyScore * 100).toFixed(0) }}</td>
                <td class="px-5 py-3 text-right font-mono text-[var(--muted)]">{{ node.absScoreDisplay }}</td>
                <td class="px-5 py-3 text-right">
                  <span :class="node.zscore > 0 ? 'text-[var(--red)]' : 'text-[var(--green)]'">
                    {{ node.zscore > 0 ? t('analysis.high') : t('analysis.low') }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      </Paywall>

      <!-- Section 4: Full Report — WeChat HTML format, Pro only -->
      <div class="mb-12 fade-in fade-in-delay-3" v-if="reportStore.latest">
        <div class="flex items-center justify-between mb-6">
          <div>
            <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Full Report</p>
            <h2 class="text-lg font-light text-white">{{ t('analysis.report') }}</h2>
          </div>
          <button @click="showFullReport = !showFullReport"
                  class="text-xs text-[var(--accent)] hover:text-white transition-colors px-3 py-1.5 rounded border border-[var(--border)] hover:border-[var(--accent)]">
            {{ showFullReport ? t('common.collapse') : t('common.expand') }}
          </button>
        </div>
        <div v-show="showFullReport" class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4">
          <!-- Prefer WeChat HTML (better formatting), fallback to Markdown -->
          <div v-if="lang === 'zh' && socialContent.wechat" class="flex justify-center">
            <div class="w-full max-w-[640px] rounded-xl overflow-hidden">
              <iframe :srcdoc="socialContent.wechat" class="w-full border-0" style="height:800px" sandbox="allow-same-origin"></iframe>
            </div>
          </div>
          <div v-else class="prose prose-invert prose-sm max-w-none" v-html="renderedMarkdown"></div>
        </div>
      </div>

      <!-- Section 6: Share & Export -->
      <div class="mb-12 fade-in">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Share & Export</p>
        <h2 class="text-lg font-light text-white mb-6">{{ t('analysis.share') }}</h2>

        <div v-if="lang === 'en'" class="flex gap-3">
          <button @click="copyText(englishFullReportMarkdown)"
                  class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm bg-[var(--card)] border border-[var(--border)] text-[var(--muted)] hover:text-white">
            {{ copied ? t('analysis.copied') : t('analysis.copyBrief') }}
          </button>
          <a :href="'data:text/markdown;charset=utf-8,' + encodeURIComponent(englishFullReportMarkdown)"
             download="gfcri-daily-risk-brief.md"
             class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm bg-[var(--accent)]/15 text-[var(--accent)] hover:bg-[var(--accent)]/25">
            {{ t('analysis.downloadMarkdown') }}
          </a>
        </div>

        <div v-else class="flex gap-3">
          <button @click="activeExport = activeExport === 'wechat' ? '' : 'wechat'"
                  class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm transition-all"
                  :class="activeExport === 'wechat' ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'bg-[var(--card)] border border-[var(--border)] text-[var(--muted)] hover:text-white'">
            💬 {{ lang === 'zh' ? '微信文章' : 'WeChat' }}
          </button>
          <button @click="activeExport = activeExport === 'zsxq' ? '' : 'zsxq'"
                  class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm transition-all"
                  :class="activeExport === 'zsxq' ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'bg-[var(--card)] border border-[var(--border)] text-[var(--muted)] hover:text-white'">
            🌟 {{ lang === 'zh' ? '知识星球' : 'Zsxq' }}
          </button>
          <button @click="activeExport = activeExport === 'card' ? '' : 'card'"
                  class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm transition-all"
                  :class="activeExport === 'card' ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'bg-[var(--card)] border border-[var(--border)] text-[var(--muted)] hover:text-white'">
            🖼️ {{ lang === 'zh' ? '分享卡片' : 'Card' }}
          </button>
        </div>

        <!-- WeChat Preview -->
        <div v-if="lang === 'zh' && activeExport === 'wechat' && socialContent.wechat" class="mt-4 bg-[var(--card)] border border-[var(--border)] rounded-xl overflow-hidden">
          <div class="flex items-center justify-between px-5 py-3 border-b border-[var(--border)]">
            <span class="text-xs text-[var(--muted)]">{{ lang === 'zh' ? '微信公众号文章预览' : 'WeChat Article Preview' }}</span>
            <a :href="'data:text/html;charset=utf-8,' + encodeURIComponent(socialContent.wechat)"
               download="gfcri_wechat.html"
               class="text-xs text-[var(--accent)] hover:text-white transition-colors"> {{ lang === 'zh' ? '下载 HTML' : 'Download HTML' }} </a>
          </div>
          <div class="p-4 flex justify-center">
            <div class="max-w-[375px] w-full rounded-2xl overflow-hidden border border-[var(--border)]">
              <iframe :srcdoc="socialContent.wechat" class="w-full" style="height:600px" sandbox="allow-same-origin"></iframe>
            </div>
          </div>
        </div>

        <!-- Zsxq Preview -->
        <div v-if="lang === 'zh' && activeExport === 'zsxq' && socialContent.zsxq" class="mt-4 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs text-[var(--muted)]">{{ lang === 'zh' ? '知识星球帖子' : 'Zsxq Post' }}</span>
            <button @click="copyText(socialContent.zsxq)" class="text-xs text-[var(--accent)] hover:text-white transition-colors">
              {{ copied ? (lang === 'zh' ? '已复制 ✓' : 'Copied ✓') : (lang === 'zh' ? '复制原文' : 'Copy') }}
            </button>
          </div>
          <pre class="text-xs text-[var(--muted)] whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto">{{ socialContent.zsxq }}</pre>
        </div>

        <!-- Card Preview -->
        <div v-if="lang === 'zh' && activeExport === 'card' && socialContent.cardUrl" class="mt-4 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 flex justify-center">
          <img :src="socialContent.cardUrl" alt="Share Card" class="max-w-[400px] rounded-xl shadow-lg" />
        </div>
      </div>

    </template>

    <div v-else class="text-[var(--muted)] text-center py-20 text-sm">{{ t("common.noData") }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import MarkdownIt from 'markdown-it'

import { useRiskStore } from '@/stores/risk'
import { useReportStore } from '@/stores/report'
import { COLORS } from '@/composables/useTheme'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Paywall from '@/components/common/Paywall.vue'
import RiskWatch from '@/components/common/RiskWatch.vue'
import client from '@/api/client'

use([BarChart, LineChart, GridComponent, TooltipComponent, MarkLineComponent, CanvasRenderer])

const md = new MarkdownIt()
const riskStore = useRiskStore()
const reportStore = useReportStore()
const { isPro } = useAuth()
const { t, tx, lang } = useI18n()
const showFullReport = ref(false)
const activeExport = ref('')
const copied = ref(false)
const socialContent = ref<{ wechat: string; zsxq: string; cardUrl: string }>({ wechat: '', zsxq: '', cardUrl: '' })
const enNarrative = ref('')

onMounted(async () => {
  riskStore.loadLatest()
  riskStore.loadHistory()
  reportStore.loadLatest()
  try {
    const [wRes, zRes, enRes] = await Promise.allSettled([
      client.get('/social/wechat/latest'),
      client.get('/social/zsxq/latest'),
      client.get('/intraday/narrative-en'),
    ])
    if (wRes.status === 'fulfilled') socialContent.value.wechat = wRes.value.data?.content || ''
    if (zRes.status === 'fulfilled') socialContent.value.zsxq = zRes.value.data?.content || ''
    if (enRes.status === 'fulfilled') enNarrative.value = enRes.value.data?.content || ''
  } catch {}
})

function copyText(text: string) {
  navigator.clipboard.writeText(text)
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}

const nodeNames: Record<string, string> = {
  fed_funds: '美联储利率', ust_10y: '10年美债', ust_2y: '2年美债', dxy: '美元',
  krw_usd: '韩元', kospi: '韩股', vix: '恐慌指数', spx: '标普500',
  hyg: '高收益债', lqd: '投资级债', kre: '银行股', vnq: '房地产',
  oil_wti: '原油', gold: '黄金', copper: '铜', hsi: '恒生',
  eurusd: '欧元', cny_usd: '人民币', jpy_usd: '日元', nikkei: '日经',
  sox: '半导体', stoxx50: '欧股', eem: '新兴市场', emb: '新兴债',
  btc: '比特币', italy_etf: '意大利', kr_cds_5y: '韩国信用',
  consumer_stress: '消费压力', us_recession_prob: '衰退概率',
  ai_capex: 'AI投资', dram_spot: 'DRAM', nand_spot: 'NAND',
  natgas: '天然气', wheat: '小麦', bdry: '干散货',
}

const renderedNarrative = computed(() => {
  const narr = lang.value === 'en' && enNarrative.value
    ? enNarrative.value
    : reportStore.latest?.llm_narrative
  return narr ? md.render(narr) : ''
})

const truncatedNarrative = computed(() => {
  const narr = lang.value === 'en' && enNarrative.value
    ? enNarrative.value
    : reportStore.latest?.llm_narrative
  if (!narr) return ''
  const paragraphs = narr.split('\n\n').filter((p: string) => p.trim())
  return md.render(paragraphs.slice(0, 2).join('\n\n'))
})

const renderedMarkdown = computed(() => {
  if (lang.value === 'en') return md.render(englishFullReportMarkdown.value)
  return reportStore.latest ? md.render(reportStore.latest.report_markdown) : ''
})

const englishFullReportMarkdown = computed(() => {
  const risk = riskStore.latest
  if (!risk) return 'No report data available.'

  const lines: string[] = []
  const alert = t(`alert.${risk.alert_level}`)
  const coherence = (risk.coherence_multiplier || 1).toFixed(2)

  lines.push(`# GFCRI Daily Report`)
  lines.push('')
  lines.push(`**Date:** ${risk.index_date}`)
  lines.push(`**Risk Index:** ${risk.gfcri_value.toFixed(1)} / 100 (${alert})`)
  lines.push(`**Coherence Multiplier:** ${coherence}x`)
  lines.push('')

  lines.push(`## Key Judgment`)
  if (enNarrative.value.trim()) {
    lines.push(enNarrative.value.trim())
  } else {
    const active = activeChains.value.length
    const anomalies = anomalousNodes.value.length
    lines.push(
      `GFCRI is at ${risk.gfcri_value.toFixed(1)}, with ${active} active transmission ` +
      `${active === 1 ? 'chain' : 'chains'} and ${anomalies} anomalous ` +
      `${anomalies === 1 ? 'indicator' : 'indicators'}.`
    )
  }
  lines.push('')

  const subDetails = risk.sub_index_details || {}
  const subEntries = Object.entries(subDetails)
    .map(([key, val]: [string, any]) => ({
      name: tx(val?.name || key),
      score: Number(val?.score || 0),
      driver: tx(val?.top_driver || val?.driver || ''),
    }))
    .sort((a, b) => b.score - a.score)
  if (subEntries.length) {
    lines.push(`## Sub-Index Scores`)
    lines.push('')
    lines.push(`| Sub-index | Score | Main Driver |`)
    lines.push(`|---|---:|---|`)
    for (const item of subEntries) {
      lines.push(`| ${item.name} | ${item.score.toFixed(1)} | ${item.driver || '-'} |`)
    }
    lines.push('')
  }

  if (activeChains.value.length) {
    lines.push(`## Active Transmission Chains`)
    lines.push('')
    for (const chain of activeChains.value) {
      const path = (chain.path || []).map((n: string) => tx(nodeNames[n] || n)).join(' -> ')
      lines.push(`- **${tx(chain.name)}** (${Number(chain.stress || 0).toFixed(0)}): ${path}`)
      if (chain.description) lines.push(`  ${tx(chain.description)}`)
    }
    lines.push('')
  } else {
    lines.push(`## Active Transmission Chains`)
    lines.push('')
    lines.push(`No active transmission chains are currently detected.`)
    lines.push('')
  }

  lines.push(`## Anomalous Indicators`)
  lines.push('')
  if (anomalousNodes.value.length) {
    lines.push(`| Indicator | Current | Deviation | Direction |`)
    lines.push(`|---|---:|---:|---|`)
    for (const node of anomalousNodes.value) {
      const direction = node.zscore > 0 ? 'High' : 'Low'
      const value = typeof node.value === 'number' ? node.value.toFixed(2) : '-'
      lines.push(`| ${tx(node.name)} | ${value} | ${Math.abs(node.zscore).toFixed(1)}x | ${direction} |`)
    }
  } else {
    lines.push(`No indicators are currently outside the anomaly threshold.`)
  }
  lines.push('')

  const history = [...riskStore.history].reverse().slice(-7)
  if (history.length > 1) {
    lines.push(`## Recent GFCRI Trend`)
    lines.push('')
    lines.push(`| Date | GFCRI | Alert |`)
    lines.push(`|---|---:|---|`)
    for (const row of history) {
      lines.push(`| ${row.index_date} | ${Number(row.gfcri_value).toFixed(1)} | ${t(`alert.${row.alert_level}`)} |`)
    }
    lines.push('')
  }

  lines.push(`## Notes`)
  lines.push('')
  lines.push(`This English report is generated from the structured GFCRI data available in the dashboard. It avoids the Chinese social-publishing report format when English mode is selected.`)

  return lines.join('\n')
})

const sortedChains = computed(() => {
  const chains = riskStore.latest?.chain_details
  if (!chains) return []
  const list = Array.isArray(chains) ? chains : Object.values(chains)
  return [...list].sort((a: any, b: any) => {
    if (a.active !== b.active) return a.active ? -1 : 1
    return b.stress - a.stress
  })
})

const activeChains = computed(() => sortedChains.value.filter((c: any) => c.active))
const dormantChains = computed(() => sortedChains.value.filter((c: any) => !c.active))

const anomalousNodes = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return []
  return Object.entries(nc)
    .filter(([, info]: [string, any]) => info.is_anomalous)
    .map(([id, info]: [string, any]) => ({
      id, name: info.display_name || nodeNames[id] || id,
      zscore: Number(info.zscore || 0),
      value: info.current_value,
      anomalyScore: Number(info.anomaly_score || 0),
      absScore: info.abs_score === null || info.abs_score === undefined ? null : Number(info.abs_score),
      absScoreDisplay: info.abs_score === null || info.abs_score === undefined ? '-' : (Number(info.abs_score) * 100).toFixed(0),
    }))
    .sort((a, b) => Math.abs(b.zscore) - Math.abs(a.zscore))
})

const topNodeContributions = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return []
  return Object.entries(nc)
    .map(([id, info]: [string, any]) => {
      const zscore = Number(info.zscore || 0)
      const anomaly = Number(info.anomaly_score || 0)
      const absScore = info.abs_score === null || info.abs_score === undefined ? null : Number(info.abs_score)
      return {
        id,
        name: tx(info.display_name || nodeNames[id] || id),
        zscore,
        anomalyScore: anomaly,
        absScore,
        absScoreDisplay: absScore === null ? '-' : (absScore * 100).toFixed(0),
        currentDisplay: formatCurrentValue(info.current_value),
        sortScore: Math.max(Math.abs(zscore) / 4, anomaly, absScore || 0),
      }
    })
    .sort((a, b) => b.sortScore - a.sortScore)
    .slice(0, 8)
})

const subIndexRows = computed(() => {
  const details = riskStore.latest?.sub_index_details || {}
  return Object.entries(details)
    .map(([key, val]: [string, any]) => ({
      id: key,
      name: tx(val?.name || key),
      score: Number(val?.score || 0),
      anomalyStress: Number(val?.mean_stress || 0) * 100,
      absoluteStress: Number(val?.mean_abs_stress || 0) * 100,
      transmission: Number(val?.transmission || 0) * 100,
      topDriver: tx(nodeNames[val?.top_driver] || val?.top_driver || '-'),
    }))
    .sort((a, b) => b.score - a.score)
})

const subIndexBreakdownOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    backgroundColor: '#111214',
    borderColor: 'rgba(255,255,255,0.08)',
    textStyle: { color: '#eff1f5', fontSize: 11 },
  },
  legend: {
    top: 0,
    right: 0,
    textStyle: { color: '#8a93a3', fontSize: 10 },
    itemWidth: 9,
    itemHeight: 9,
  },
  grid: { left: 126, right: 18, top: 34, bottom: 18 },
  xAxis: {
    type: 'value',
    max: 100,
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    axisLabel: { color: '#8a93a3', fontSize: 10 },
  },
  yAxis: {
    type: 'category',
    data: subIndexRows.value.map(r => r.name),
    axisLabel: { color: '#d6d9df', fontSize: 10, width: 112, overflow: 'truncate' },
    axisLine: { show: false },
    axisTick: { show: false },
  },
  series: [
    {
      name: t('analysis.anomalyStress'),
      type: 'bar',
      stack: 'stress',
      data: subIndexRows.value.map(r => Math.min(r.anomalyStress, 100)),
      itemStyle: { color: COLORS.yellow },
      barWidth: 12,
    },
    {
      name: t('analysis.absoluteStress'),
      type: 'bar',
      stack: 'stress',
      data: subIndexRows.value.map(r => Math.min(r.absoluteStress, 100)),
      itemStyle: { color: COLORS.orange },
      barWidth: 12,
    },
    {
      name: t('analysis.transmissionAmp'),
      type: 'bar',
      stack: 'stress',
      data: subIndexRows.value.map(r => Math.min(r.transmission, 100)),
      itemStyle: { color: COLORS.blue },
      barWidth: 12,
    },
  ],
}))

const chainPressureRows = computed(() => {
  return sortedChains.value.map((chain: any) => ({
    id: chain.id,
    name: tx(chain.name),
    path: (chain.path || []).map((n: string) => tx(nodeNames[n] || n)).join(' -> '),
    stress: Number(chain.stress || 0),
    pathStrength: Number(chain.path_strength || 0).toFixed(4),
  }))
})

function chainNodeBars(chain: any) {
  const scores = chain.node_scores || {}
  return (chain.path || []).map((id: string) => {
    const score = Number(scores[id] || 0)
    return {
      id,
      name: tx(nodeNames[id] || id),
      score,
      width: Math.min(score * 100, 100),
    }
  })
}

function formatCurrentValue(value: any): string {
  if (value === null || value === undefined) return '-'
  const n = Number(value)
  if (!Number.isFinite(n)) return String(value)
  if (Math.abs(n) >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 0 })
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

function scoreColor(score: number): string {
  if (score >= 70) return COLORS.red
  if (score >= 45) return COLORS.orange
  if (score >= 25) return COLORS.yellow
  return COLORS.green
}

const trendChartOption = computed(() => {
  const data = [...riskStore.history].reverse()
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#111214',
      borderColor: 'rgba(255,255,255,0.06)',
      textStyle: { color: '#eff1f5', fontSize: 12 },
    },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: data.map(d => d.index_date), axisLabel: { color: '#6b7280', fontSize: 10 } },
    yAxis: {
      type: 'value', min: 0, max: 100,
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
      axisLabel: { color: '#6b7280' },
    },
    series: [{
      type: 'line',
      data: data.map(d => d.gfcri_value),
      smooth: true,
      lineStyle: { color: COLORS.accent, width: 2 },
      areaStyle: { color: COLORS.accent + '10' },
      markLine: {
        silent: true, symbol: 'none',
        lineStyle: { type: 'dashed' },
        data: [
          { yAxis: 25, lineStyle: { color: COLORS.green + '60' } },
          { yAxis: 50, lineStyle: { color: COLORS.yellow + '60' } },
          { yAxis: 75, lineStyle: { color: COLORS.red + '60' } },
        ],
      },
    }],
  }
})
</script>

<style scoped>
.judgment-markdown :deep(h1),
.judgment-markdown :deep(h2),
.judgment-markdown :deep(h3) {
  font-size: 15px;
  line-height: 1.45;
  margin-top: 0.8em;
  margin-bottom: 0.45em;
}

.judgment-markdown :deep(p),
.judgment-markdown :deep(li) {
  color: var(--muted);
  line-height: 1.65;
}

.judgment-markdown :deep(ul),
.judgment-markdown :deep(ol) {
  padding-left: 1.2em;
}
</style>
