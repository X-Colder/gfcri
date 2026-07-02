<template>
  <div class="space-y-6">
    <h2 class="text-xl font-bold">{{ t('briefing.title') }}</h2>

    <LoadingSpinner v-if="riskStore.loading || reportStore.loading" />

    <template v-else-if="riskStore.latest">
      <div class="grid grid-cols-5 gap-3">
        <MetricCard
          label="GFCRI"
          :value="riskStore.latest.gfcri_value.toFixed(1)"
          :color="getAlertColor(riskStore.latest.alert_level)"
        />
        <MetricCard :label="t('briefing.alertStatus')" :value="t('alert.' + riskStore.latest.alert_level)" :color="getAlertColor(riskStore.latest.alert_level)" />
        <MetricCard :label="t('briefing.anomalyNodes')" :value="anomalyCount" />
        <MetricCard :label="t('briefing.date')" :value="riskStore.latest.index_date" />
        <MetricCard :label="t('briefing.coherence')" :value="(riskStore.latest.coherence_multiplier || 1).toFixed(2)" />
      </div>

      <!-- Z-Score Chart -->
      <div class="bg-card border border-border rounded-xl p-6">
        <h3 class="text-sm font-medium text-muted mb-4">{{ t('briefing.zscore') }}</h3>
        <v-chart :option="zscoreChartOption" style="height: 400px" autoresize />
      </div>

      <!-- Report Markdown -->
      <div v-if="reportStore.latest" class="bg-card border border-border rounded-xl p-6">
        <h3 class="text-sm font-medium text-muted mb-4">{{ t('briefing.reportDetail') }}</h3>
        <div class="prose prose-invert prose-sm max-w-none" v-html="renderedMarkdown"></div>
      </div>

      <!-- Trend Chart -->
      <div v-if="riskStore.history.length > 1" class="bg-card border border-border rounded-xl p-6">
        <h3 class="text-sm font-medium text-muted mb-4">{{ t('analysis.trend') }}</h3>
        <v-chart :option="trendChartOption" style="height: 250px" autoresize />
      </div>
    </template>

    <div v-else class="text-muted text-center py-12">{{ t('common.noData') }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import MarkdownIt from 'markdown-it'

import { useRiskStore } from '@/stores/risk'
import { useReportStore } from '@/stores/report'
import { COLORS, getAlertColor } from '@/composables/useTheme'
import MetricCard from '@/components/common/MetricCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useI18n } from '@/composables/useI18n'

use([BarChart, LineChart, GridComponent, TooltipComponent, MarkLineComponent, CanvasRenderer])

const md = new MarkdownIt()
const riskStore = useRiskStore()
const reportStore = useReportStore()
const { t, tx } = useI18n()

onMounted(() => {
  riskStore.loadLatest()
  riskStore.loadHistory()
  reportStore.loadLatest()
})

const anomalyCount = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return 0
  return Object.values(nc).filter((n: any) => n.is_anomalous).length
})

const renderedMarkdown = computed(() => {
  if (!reportStore.latest) return ''
  return md.render(reportStore.latest.report_markdown)
})

const zscoreChartOption = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return {}

  const entries = Object.entries(nc)
    .map(([id, info]: [string, any]) => ({ id, name: tx(info.display_name || id), zscore: info.zscore || 0 }))
    .sort((a, b) => Math.abs(b.zscore) - Math.abs(a.zscore))
    .slice(0, 15)

  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 120, right: 40, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#2d333b' } },
      axisLabel: { color: '#8b949e' },
    },
    yAxis: { type: 'category', data: entries.map(e => e.name), axisLabel: { color: '#e6edf3', fontSize: 11 } },
    series: [{
      type: 'bar',
      data: entries.map(e => ({
        value: e.zscore,
        itemStyle: { color: Math.abs(e.zscore) > 2 ? COLORS.red : Math.abs(e.zscore) > 1 ? COLORS.yellow : COLORS.green },
      })),
      barWidth: 16,
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { type: 'dashed', color: COLORS.red },
        data: [{ xAxis: 2 }, { xAxis: -2 }],
      },
    }],
  }
})

const trendChartOption = computed(() => {
  const data = [...riskStore.history].reverse()
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: data.map(d => d.index_date), axisLabel: { color: '#8b949e', fontSize: 10 } },
    yAxis: { type: 'value', min: 0, max: 100, splitLine: { lineStyle: { color: '#2d333b' } }, axisLabel: { color: '#8b949e' } },
    series: [{
      type: 'line',
      data: data.map(d => d.gfcri_value),
      smooth: true,
      lineStyle: { color: COLORS.blue },
      areaStyle: { color: COLORS.blue + '1a' },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { type: 'dashed' },
        data: [
          { yAxis: 25, lineStyle: { color: COLORS.green } },
          { yAxis: 50, lineStyle: { color: COLORS.yellow } },
          { yAxis: 75, lineStyle: { color: COLORS.red } },
        ],
      },
    }],
  }
})
</script>
