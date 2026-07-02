<template>
  <div v-if="chartOption.series" style="height: 450px; width: 100%;">
    <v-chart :option="chartOption" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useRiskStore } from '@/stores/risk'
import { COLORS } from '@/composables/useTheme'
import { useI18n } from '@/composables/useI18n'

use([GraphChart, TooltipComponent, CanvasRenderer])

const riskStore = useRiskStore()
const { tx } = useI18n()

const NODE_NAMES: Record<string, string> = {
  fed_funds: '美联储利率', ust_10y: '10Y美债', ust_2y: '2Y美债', dxy: '美元',
  krw_usd: '韩元', kospi: '韩股', vix: 'VIX', spx: '标普500',
  hyg: '高收益债', lqd: '投资级债', kre: '银行股', vnq: '房地产',
  oil_wti: '原油', gold: '黄金', copper: '铜', hsi: '恒生',
  eurusd: '欧元', cny_usd: '人民币', jpy_usd: '日元', nikkei: '日经',
  sox: '半导体', stoxx50: '欧股', eem: '新兴市场', emb: '新兴债',
  btc: '比特币', italy_etf: '意大利', kr_cds_5y: '韩国CDS',
}

const chartOption = computed(() => {
  const nc = riskStore.latest?.node_contributions
  const chains = riskStore.latest?.chain_details
  if (!nc || !chains) return {}

  // Build nodes from top 20 contributors
  const entries = Object.entries(nc)
    .map(([id, info]: [string, any]) => ({
      id, name: tx(NODE_NAMES[id] || info.display_name || id),
      anomaly: info.anomaly_score || 0, isAnomaly: info.is_anomalous,
    }))
    .sort((a, b) => b.anomaly - a.anomaly)
    .slice(0, 20)

  const nodeIds = new Set(entries.map(e => e.id))

  const nodes = entries.map(e => ({
    id: e.id,
    name: e.name,
    symbolSize: 20 + e.anomaly * 30,
    itemStyle: {
      color: e.isAnomaly ? COLORS.red : e.anomaly > 0.3 ? COLORS.yellow : COLORS.green,
      shadowColor: e.isAnomaly ? 'rgba(239,68,68,0.6)' : 'transparent',
      shadowBlur: e.isAnomaly ? 15 : 0,
    },
    label: { show: true, fontSize: 10, color: '#eff1f5' },
  }))

  // Build edges from chain paths
  const edges: any[] = []
  const chainList = Array.isArray(chains) ? chains : Object.values(chains)
  for (const chain of chainList) {
    const path = chain.path || []
    const active = chain.active
    for (let i = 0; i < path.length - 1; i++) {
      const src = path[i]
      const tgt = path[i + 1]
      if (nodeIds.has(src) && nodeIds.has(tgt)) {
        edges.push({
          source: src,
          target: tgt,
          lineStyle: {
            color: active ? COLORS.red : 'rgba(255,255,255,0.08)',
            width: active ? 2.5 : 1,
            curveness: 0.2,
          },
        })
      }
    }
  }

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: '#111214',
      borderColor: 'rgba(255,255,255,0.06)',
      textStyle: { color: '#eff1f5', fontSize: 11 },
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      edges,
      roam: true,
      force: { repulsion: 400, gravity: 0.1, edgeLength: [80, 200] },
      lineStyle: { opacity: 0.8 },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 },
      },
    }],
  }
})
</script>
