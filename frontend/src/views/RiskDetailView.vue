<template>
  <div class="space-y-6">
    <h2 class="text-xl font-bold">{{ t('risk.title') }}</h2>

    <LoadingSpinner v-if="riskStore.loading" />

    <template v-else-if="riskStore.latest">
      <!-- Gauge -->
      <div class="grid grid-cols-2 gap-6">
        <div class="bg-card border border-border rounded-xl p-6">
          <v-chart :option="gaugeOption" style="height: 280px" autoresize />
        </div>
        <div class="grid grid-cols-2 gap-3 content-start">
          <MetricCard
            v-for="(si, key) in subIndices"
            :key="key"
            :label="tx(si.name)"
            :value="si.score.toFixed(1)"
            :subtitle="'Top: ' + tx(si.top_driver || '-')"
            :color="si.score >= 50 ? COLORS.orange : COLORS.green"
          />
        </div>
      </div>

      <!-- Transmission Chains -->
      <div class="bg-card border border-border rounded-xl p-6">
        <h3 class="text-sm font-medium text-muted mb-4">{{ t('risk.chainStatus') }}</h3>
        <table class="w-full text-sm">
          <thead>
            <tr class="text-muted border-b border-border">
              <th class="text-left py-2 px-3">{{ t('industry.edges') }}</th>
              <th class="text-left py-2 px-3">{{ t('common.path') }}</th>
              <th class="text-left py-2 px-3">{{ t('globe.pressure') }}</th>
              <th class="text-left py-2 px-3">{{ t('common.status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="chain in chainList" :key="chain.id" class="border-b border-border/50">
              <td class="py-2 px-3">{{ tx(chain.name) }}</td>
              <td class="py-2 px-3 font-mono text-xs text-muted">{{ chain.path?.map((p: string) => tx(p)).join(' → ') }}</td>
              <td class="py-2 px-3">
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-2 bg-bg rounded-full overflow-hidden">
                    <div class="h-full rounded-full" :style="{ width: chain.stress + '%', backgroundColor: chain.stress > 60 ? COLORS.red : chain.stress > 40 ? COLORS.orange : COLORS.green }"></div>
                  </div>
                  <span class="text-xs font-mono w-10 text-right">{{ chain.stress?.toFixed(0) }}</span>
                </div>
              </td>
              <td class="py-2 px-3">
                <span :class="chain.active ? 'text-alert-red' : 'text-muted'">{{ chain.active ? t('common.active') : t('common.dormant') }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- History Trend -->
      <div v-if="riskStore.history.length > 1" class="bg-card border border-border rounded-xl p-6">
        <h3 class="text-sm font-medium text-muted mb-4">{{ t('risk.history') }}</h3>
        <v-chart :option="historyOption" style="height: 250px" autoresize />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { GaugeChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { useRiskStore } from '@/stores/risk'
import { COLORS } from '@/composables/useTheme'
import MetricCard from '@/components/common/MetricCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useI18n } from '@/composables/useI18n'

use([GaugeChart, LineChart, GridComponent, TooltipComponent, MarkLineComponent, CanvasRenderer])

const riskStore = useRiskStore()
const { t, tx } = useI18n()

onMounted(() => {
  riskStore.loadLatest()
  riskStore.loadHistory()
})

const subIndices = computed(() => riskStore.latest?.sub_index_details || {})

const chainList = computed(() => {
  const cd = riskStore.latest?.chain_details
  if (!cd) return []
  return Array.isArray(cd) ? cd : Object.values(cd)
})

const gaugeOption = computed(() => ({
  series: [{
    type: 'gauge',
    startAngle: 200,
    endAngle: -20,
    min: 0,
    max: 100,
    pointer: { show: true, length: '60%', width: 4, itemStyle: { color: COLORS.text } },
    axisLine: {
      lineStyle: {
        width: 20,
        color: [[0.25, COLORS.green], [0.5, COLORS.yellow], [0.75, COLORS.orange], [1, COLORS.red]],
      },
    },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { color: COLORS.muted, fontSize: 11 },
    detail: { fontSize: 32, color: COLORS.text, offsetCenter: [0, '60%'], formatter: '{value}' },
    data: [{ value: riskStore.latest?.gfcri_value.toFixed(1) }],
  }],
}))

const historyOption = computed(() => {
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
        silent: true, symbol: 'none', lineStyle: { type: 'dashed' },
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
