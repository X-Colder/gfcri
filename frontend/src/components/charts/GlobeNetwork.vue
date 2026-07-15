<template>
  <div class="globe-wrapper">
    <!-- Left panel -->
    <div class="panel panel-left">
      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-badge">{{ t('globe.live') }}</span>
          <span class="stat-period">{{ t('globe.live') }}</span>
        </div>
        <p class="stat-number">{{ activeCount }}<span class="stat-unit"> / {{ totalChains }}</span></p>
        <p class="stat-sub">{{ t('globe.activeChains') }}</p>
      </div>

      <div v-for="chain in topActiveChains" :key="chain.id" class="chain-card">
        <div class="chain-dot" :style="{background: stressColor(chain.stress)}"></div>
        <div class="chain-info">
          <p class="chain-name">{{ tx(chain.name) }}</p>
          <p class="chain-stress">{{ t('globe.pressure') }} {{ chain.stress.toFixed(0) }}</p>
        </div>
      </div>

      <div class="stat-card mt-4">
        <p class="stat-label">{{ t('globe.anomalyCount') }}</p>
        <p class="stat-number" style="color:var(--red)">{{ anomalyCount }}</p>
        <p class="stat-sub">{{ t('globe.abnormal') }}</p>
      </div>
    </div>

    <!-- Center: 3D Globe -->
    <div class="globe-container" ref="globeRef">
      <v-chart
        :key="globeChartKey"
        ref="chartRef"
        :option="globeOption"
        :update-options="globeUpdateOptions"
        style="width:100%;height:100%"
        autoresize
      />

      <!-- HTML overlay labels by region (because scatter3D label doesn't render in WebGL) -->
      <div class="region-label region-us">
        <p class="region-title">🇺🇸 {{ t('globe.us') }}</p>
        <span v-for="n in regionNodes.us" :key="n.id" class="node-tag" :style="{color: n.color}">{{ n.label }}</span>
      </div>
      <div class="region-label region-europe">
        <p class="region-title">🇪🇺 {{ t('globe.europe') }}</p>
        <span v-for="n in regionNodes.europe" :key="n.id" class="node-tag" :style="{color: n.color}">{{ n.label }}</span>
      </div>
      <div class="region-label region-asia">
        <p class="region-title">🌏 {{ t('globe.asia') }}</p>
        <span v-for="n in regionNodes.asia" :key="n.id" class="node-tag" :style="{color: n.color}">{{ n.label }}</span>
      </div>
      <div class="region-label region-commodity">
        <p class="region-title">📦 {{ t('globe.commodity') }}</p>
        <span v-for="n in regionNodes.commodity" :key="n.id" class="node-tag" :style="{color: n.color}">{{ n.label }}</span>
      </div>

      <div class="floating-card">
        <p class="floating-label">GFCRI</p>
        <p class="floating-value" :style="{color: gfcriColor}">{{ gfcriValue.toFixed(1) }}</p>
        <p class="floating-sub">/ 100</p>
      </div>
      <!-- Legend -->
      <div class="globe-legend">
        <span><i style="background:#ef4444"></i>{{ t('globe.highPressure') }}</span>
        <span><i style="background:#f97316"></i>{{ t('globe.medPressure') }}</span>
        <span><i style="background:#fbbf24"></i>{{ t('globe.attention') }}</span>
        <span><i style="background:#34d399"></i>{{ t('globe.normal') }}</span>
        <span style="margin-left:6px">── {{ t('globe.activeLine') }}</span>
        <span>╌╌ {{ t('globe.dormantLine') }}</span>
      </div>
    </div>

    <!-- Right panel -->
    <div class="panel panel-right">
      <div class="stat-card">
        <p class="stat-label">Risk Trend</p>
        <p class="stat-number" :style="{color: gfcriColor}">{{ gfcriValue.toFixed(1) }}</p>
        <p class="stat-sub" v-if="gfcriDelta">
          <span :style="{color: gfcriDelta > 0 ? 'var(--red)' : 'var(--green)'}">
            {{ gfcriDelta > 0 ? '↑' : '↓' }} {{ Math.abs(gfcriDelta).toFixed(1) }}
          </span> {{ t('globe.vsYesterday') }}
        </p>
      </div>

      <div class="stat-card">
        <p class="stat-label">{{ t('globe.riskDist') }}</p>
        <div class="donut-row">
          <div class="donut-item">
            <svg viewBox="0 0 36 36" class="donut-svg">
              <path class="donut-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
              <path class="donut-fill" :style="{stroke:'var(--red)', strokeDasharray: activeRatio+' '+(100-activeRatio)}" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
            </svg>
            <span class="donut-label">{{ activeRatio.toFixed(0) }}%</span>
          </div>
          <div class="donut-item">
            <svg viewBox="0 0 36 36" class="donut-svg">
              <path class="donut-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
              <path class="donut-fill" :style="{stroke:'var(--green)', strokeDasharray: (100-activeRatio)+' '+activeRatio}" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
            </svg>
            <span class="donut-label">{{ (100-activeRatio).toFixed(0) }}%</span>
          </div>
        </div>
        <div class="donut-legend">
          <span><i style="background:var(--red)"></i>{{ t('globe.active') }}</span>
          <span><i style="background:var(--green)"></i>{{ t('globe.dormant') }}</span>
        </div>
      </div>

      <div class="stat-card">
        <p class="stat-label">{{ t('globe.regionStress') }}</p>
        <div class="region-bars">
          <div v-for="r in regionStress" :key="r.name" class="region-bar">
            <span class="region-name">{{ r.name }}</span>
            <div class="region-track"><div class="region-fill" :style="{width: r.pct+'%', background: stressColor(r.stress)}"></div></div>
            <span class="region-val">{{ r.stress.toFixed(0) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import * as echarts from 'echarts'
import 'echarts-gl'
import VChart from 'vue-echarts'
import { useRiskStore } from '@/stores/risk'
import { getAlertColor } from '@/composables/useTheme'
import { useI18n } from '@/composables/useI18n'

const riskStore = useRiskStore()
const { t, tx, lang } = useI18n()

// Register world map and create base texture
const chartRef = ref<InstanceType<typeof VChart> | null>(null)
const baseTextureReady = ref(false)
const baseTextureCanvas = shallowRef<HTMLCanvasElement | null>(null)
const globeUpdateOptions = { notMerge: true, lazyUpdate: false }
const globeChartKey = computed(() => `globe-${lang.value}-${baseTextureReady.value ? 'texture' : 'fallback'}`)
let textureChart: echarts.ECharts | null = null

async function refreshGlobeChart() {
  await nextTick()
  chartRef.value?.setOption(globeOption.value, globeUpdateOptions)
  chartRef.value?.resize()
}

onMounted(async () => {
  try {
    const resp = await fetch('/world.json')
    const worldJson = await resp.json()
    echarts.registerMap('world', worldJson)

    // Create a canvas-based map texture for the globe surface
    const canvas = document.createElement('canvas')
    canvas.width = 2048
    canvas.height = 1024
    textureChart = echarts.init(canvas, undefined, { width: 2048, height: 1024 })
    textureChart.setOption({
      backgroundColor: '#0a1628',
      geo: {
        type: 'map',
        map: 'world',
        left: 0, right: 0, top: 0, bottom: 0,
        boundingCoords: [[-180, 90], [180, -90]],
        itemStyle: {
          areaColor: '#0f1d32',
          borderColor: '#1e40af',
          borderWidth: 0.8,
        },
        emphasis: { disabled: true },
        silent: true,
      },
    }, globeUpdateOptions)
    baseTextureCanvas.value = markRaw(canvas)
    baseTextureReady.value = true
    refreshGlobeChart()
  } catch (e) {
    console.warn('World map load failed:', e)
    baseTextureReady.value = true
  }
})

watch(lang, () => {
  refreshGlobeChart()
})

onBeforeUnmount(() => {
  textureChart?.dispose()
  textureChart = null
})

const NODE_LABELS: Record<string, string> = {
  fed_funds: '美联储', ust_10y: '美债10Y', spx: '标普500', vix: 'VIX',
  dxy: '美元', kre: '银行股', vnq: '房地产', oil_wti: '原油',
  hyg: '高收益债', lqd: '投资级债', sox: '半导体', btc: '比特币',
  eurusd: '欧元', stoxx50: '欧股', italy_etf: '意大利',
  krw_usd: '韩元', kospi: '韩股', hsi: '恒生',
  cny_usd: '人民币', jpy_usd: '日元', nikkei: '日经',
  gold: '黄金', copper: '铜', eem: '新兴市场',
  dram_spot: 'DRAM', ai_capex: 'AI投资', kr_cds_5y: '韩国CDS',
  natgas: '天然气', wheat: '小麦', emb: '新兴债', bdry: '航运',
}

const NODE_GEO: Record<string, [number, number]> = {
  fed_funds: [-77, 38.9], ust_10y: [-74, 40.7], spx: [-74, 41.2],
  vix: [-87.6, 42.2], dxy: [-79, 39], kre: [-71, 42.4], vnq: [-122.4, 37.8],
  oil_wti: [-95, 30], hyg: [-84, 34], lqd: [-80, 36], sox: [-122, 37.4],
  btc: [-105, 40], consumer_stress: [-90, 38], us_recession_prob: [-85, 36],
  eurusd: [2.4, 48.9], stoxx50: [8.7, 50.1], italy_etf: [12.5, 41.9],
  krw_usd: [127, 37.6], kospi: [127, 37], hsi: [114.2, 22.3],
  cny_usd: [116.4, 40], jpy_usd: [139.7, 35.7], nikkei: [140, 36.2],
  gold: [55, 25], copper: [-70, -23], natgas: [-98, 32],
  wheat: [37.6, 55.8], eem: [100, 14], emb: [73, 19],
  dram_spot: [127.5, 37.8], nand_spot: [127.5, 37.2],
  ai_capex: [-118, 34], kr_cds_5y: [126.5, 37.6], bdry: [1, 51.5],
}

// All possible connections between indicators (comprehensive network)
const ALL_CONNECTIONS: Array<{from: string, to: string, chainId: string}> = [
  // Fed cascade
  {from:'fed_funds', to:'ust_10y', chainId:'fed_cascade'}, {from:'ust_10y', to:'dxy', chainId:'fed_cascade'},
  {from:'dxy', to:'krw_usd', chainId:'fed_cascade'},
  // Dollar squeeze
  {from:'ust_10y', to:'dxy', chainId:'dollar_squeeze'}, {from:'dxy', to:'krw_usd', chainId:'dollar_squeeze'},
  {from:'krw_usd', to:'kospi', chainId:'dollar_squeeze'},
  // Credit contagion
  {from:'lqd', to:'hyg', chainId:'credit_contagion'}, {from:'hyg', to:'kr_cds_5y', chainId:'credit_contagion'},
  {from:'kr_cds_5y', to:'kospi', chainId:'credit_contagion'},
  // Housing bank
  {from:'vnq', to:'kre', chainId:'housing_bank_doom'}, {from:'kre', to:'vix', chainId:'housing_bank_doom'},
  // Consumer recession
  {from:'consumer_stress', to:'us_recession_prob', chainId:'consumer_recession'},
  {from:'us_recession_prob', to:'vix', chainId:'consumer_recession'}, {from:'vix', to:'krw_usd', chainId:'consumer_recession'},
  // AI semi cycle
  {from:'ai_capex', to:'dram_spot', chainId:'ai_semi_cycle'}, {from:'dram_spot', to:'kospi', chainId:'ai_semi_cycle'},
  {from:'kospi', to:'sox', chainId:'ai_semi_cycle'},
  // Safe haven
  {from:'gold', to:'dxy', chainId:'safe_haven_flight'}, {from:'dxy', to:'krw_usd', chainId:'safe_haven_flight'},
  // Europe contagion
  {from:'italy_etf', to:'eurusd', chainId:'europe_contagion'}, {from:'eurusd', to:'dxy', chainId:'europe_contagion'},
  {from:'dxy', to:'eem', chainId:'europe_contagion'},
  // China shockwave
  {from:'cny_usd', to:'hsi', chainId:'china_shockwave'}, {from:'hsi', to:'kospi', chainId:'china_shockwave'},
  // Yen carry
  {from:'jpy_usd', to:'nikkei', chainId:'yen_carry_unwind'}, {from:'nikkei', to:'vix', chainId:'yen_carry_unwind'},
  // Crypto
  {from:'btc', to:'vix', chainId:'crypto_contagion'}, {from:'vix', to:'eem', chainId:'crypto_contagion'},
  // Food energy
  {from:'wheat', to:'natgas', chainId:'food_energy_shock'}, {from:'natgas', to:'stoxx50', chainId:'food_energy_shock'},
  // Cross connections
  {from:'spx', to:'vix', chainId:''}, {from:'oil_wti', to:'stoxx50', chainId:''},
  {from:'gold', to:'btc', chainId:''}, {from:'emb', to:'eem', chainId:''},
  {from:'copper', to:'hsi', chainId:''}, {from:'nand_spot', to:'sox', chainId:''},
  {from:'bdry', to:'copper', chainId:''}, {from:'stoxx50', to:'eurusd', chainId:''},
]

const gfcriValue = computed(() => riskStore.latest?.gfcri_value || 0)
const gfcriColor = computed(() => getAlertColor(riskStore.latest?.alert_level || 'green'))
const gfcriDelta = computed(() => {
  if (riskStore.history.length < 2) return 0
  return riskStore.latest!.gfcri_value - riskStore.history[1]?.gfcri_value
})

const chains = computed(() => {
  const raw = riskStore.latest?.chain_details
  if (!raw) return []
  return Array.isArray(raw) ? raw : Object.values(raw)
})

const activeChainIds = computed(() => new Set(chains.value.filter((c: any) => c.active).map((c: any) => c.id)))

const activeCount = computed(() => chains.value.filter((c: any) => c.active).length)
const totalChains = computed(() => chains.value.length)
const topActiveChains = computed(() =>
  chains.value.filter((c: any) => c.active).sort((a: any, b: any) => b.stress - a.stress).slice(0, 5)
)
const anomalyCount = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return 0
  return Object.values(nc).filter((n: any) => n.is_anomalous).length
})
const activeRatio = computed(() => totalChains.value > 0 ? (activeCount.value / totalChains.value) * 100 : 0)

const regionStress = computed(() => {
  const sub = riskStore.latest?.sub_index_details
  if (!sub) return []
  return [
    { name: t('globe.us'), stress: sub.SI_US_EQUITY?.score || 20, pct: 0 },
    { name: t('globe.asia'), stress: sub.SI_ASIA_EQUITY?.score || 20, pct: 0 },
    { name: t('globe.europe'), stress: sub.SI_EUROPE?.score || 15, pct: 0 },
    { name: t('globe.credit'), stress: sub.SI_CREDIT?.score || 12, pct: 0 },
    { name: t('globe.fx'), stress: sub.SI_FX?.score || 18, pct: 0 },
  ].map(r => ({ ...r, pct: Math.min(r.stress, 100) })).sort((a, b) => b.stress - a.stress)
})

function stressColor(s: number): string {
  if (s >= 50) return '#ef4444'
  if (s >= 35) return '#f97316'
  if (s >= 20) return '#fbbf24'
  return '#34d399'
}

function nodeColor(id: string): string {
  const nc = riskStore.latest?.node_contributions as any
  if (!nc || !nc[id]) return '#34d399'
  const info = nc[id]
  if (info.is_anomalous) return '#ef4444'
  if (info.anomaly_score > 0.3) return '#fbbf24'
  return '#34d399'
}

const REGION_MAP: Record<string, string[]> = {
  us: ['fed_funds', 'ust_10y', 'spx', 'vix', 'dxy', 'kre', 'vnq', 'oil_wti', 'hyg', 'lqd', 'sox', 'btc'],
  europe: ['eurusd', 'stoxx50', 'italy_etf'],
  asia: ['krw_usd', 'kospi', 'hsi', 'cny_usd', 'jpy_usd', 'nikkei', 'dram_spot', 'kr_cds_5y'],
  commodity: ['gold', 'copper', 'natgas', 'wheat', 'eem', 'emb', 'bdry'],
}

const regionNodes = computed(() => {
  const result: Record<string, Array<{id: string, label: string, color: string}>> = {}
  for (const [region, ids] of Object.entries(REGION_MAP)) {
    result[region] = ids
      .filter(id => NODE_LABELS[id])
      .map(id => ({ id, label: tx(NODE_LABELS[id]), color: nodeColor(id) }))
  }
  return result
})

function chainStress(chainId: string): number {
  const chain = chains.value.find((c: any) => c.id === chainId)
  return chain ? chain.stress : 15
}

const globeOption = computed(() => {
  const nc = riskStore.latest?.node_contributions || {}

  const globeConfig: any = {
    environment: '#000',
    shading: 'lambert',
    postEffect: {
      enable: true,
      bloom: { enable: true, bloomIntensity: 0.12 },
    },
    temporalSuperSampling: { enable: true },
    light: {
      ambient: { intensity: 0.3 },
      main: { intensity: 1.0, alpha: 30, beta: -40 },
    },
    atmosphere: {
      show: true,
      offset: 5,
      color: '#1e3a5f',
      glowPower: 6,
      innerGlowPower: 2,
    },
    viewControl: {
      autoRotate: true,
      autoRotateSpeed: 1.8,
      distance: 200,
      minDistance: 140,
      maxDistance: 350,
      alpha: 10,
      beta: 160,
    },
    globeRadius: 80,
  }

  // Use canvas map as texture if ready, otherwise plain color
  if (baseTextureCanvas.value) {
    globeConfig.baseTexture = baseTextureCanvas.value
  } else {
    globeConfig.baseColor = '#0a1628'
    globeConfig.itemStyle = { color: '#0f1d32', borderColor: '#1e3a5f', borderWidth: 0.5 }
  }

  // Nodes
  const points = Object.entries(NODE_GEO).map(([id, [lng, lat]]) => {
    const info = (nc as any)[id]
    const anomaly = info?.anomaly_score || 0
    const isAnomaly = info?.is_anomalous || false
    return {
      name: tx(NODE_LABELS[id] || id),
      value: [lng, lat, anomaly],
      itemStyle: {
        color: isAnomaly ? '#ef4444' : anomaly > 0.3 ? '#fbbf24' : '#34d399',
        opacity: 0.95,
        borderColor: 'rgba(255,255,255,0.4)',
        borderWidth: 0.5,
      },
      label: {
        show: true,
        formatter: tx(NODE_LABELS[id] || ''),
        fontSize: 10,
        color: isAnomaly ? '#fca5a5' : '#d1d5db',
        distance: 10,
        textBorderColor: 'rgba(0,0,0,0.8)',
        textBorderWidth: 2,
      },
    }
  })

  // Lines — ALL connections, with style based on active/dormant + stress
  const lines = ALL_CONNECTIONS
    .filter(conn => NODE_GEO[conn.from] && NODE_GEO[conn.to])
    .map(conn => {
      const isActive = conn.chainId && activeChainIds.value.has(conn.chainId)
      const stress = conn.chainId ? chainStress(conn.chainId) : 10
      const color = stressColor(stress)

      return {
        coords: [NODE_GEO[conn.from], NODE_GEO[conn.to]],
        lineStyle: {
          color: isActive ? color : 'rgba(147,197,253,0.35)',
          width: isActive ? 2.5 : 1,
          opacity: isActive ? 0.85 : 0.5,
          type: isActive ? 'solid' as const : [4, 4] as any,
        },
        effect: {
          show: true,
          period: isActive ? 3 + Math.random() * 2 : 10 + Math.random() * 5,
          trailLength: isActive ? 0.5 : 0.15,
          symbolSize: isActive ? 4.5 : 1.5,
          color: isActive ? color : 'rgba(147,197,253,0.3)',
        },
      }
    })

  return {
    globe: globeConfig,
    series: [
      {
        type: 'scatter3D',
        coordinateSystem: 'globe',
        data: points,
        symbolSize: (val: any) => 8 + (val[2] || 0) * 20,
        itemStyle: { borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.3)' },
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => params.name || '',
          fontSize: 11,
          distance: 12,
          color: '#e2e8f0',
          textBorderColor: 'rgba(0,0,0,0.9)',
          textBorderWidth: 3,
        },
        emphasis: {
          label: { show: true, fontSize: 14, color: '#fff', fontWeight: 'bold' },
          itemStyle: { borderColor: '#fff', borderWidth: 2 },
        },
      },
      {
        type: 'lines3D',
        coordinateSystem: 'globe',
        data: lines,
        blendMode: 'lighter',
      },
    ],
  }
})
</script>

<style scoped>
.globe-wrapper { display: grid; grid-template-columns: 200px 1fr 220px; gap: 16px; height: 620px; position: relative; }
.panel { display: flex; flex-direction: column; gap: 10px; padding: 8px 0; z-index: 2; }
.globe-container { position: relative; border-radius: 16px; overflow: hidden; background: #000; }
.floating-card { position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%); background: rgba(17,18,20,0.85); backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 10px 18px; text-align: center; z-index: 10; }
.floating-label { font-size: 9px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); }
.floating-value { font-size: 28px; font-weight: 200; font-family: 'JetBrains Mono', monospace; }
.floating-sub { font-size: 10px; color: var(--muted); }
.globe-legend { position: absolute; bottom: 16px; right: 16px; display: flex; gap: 8px; font-size: 8px; color: rgba(156,163,175,0.6); z-index: 10; }
.globe-legend i { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 3px; vertical-align: middle; }

/* Region overlay labels */
.region-label { position: absolute; z-index: 10; max-width: 140px; }
.region-label .region-title { font-size: 9px; color: rgba(255,255,255,0.5); margin-bottom: 3px; letter-spacing: 1px; }
.region-label .node-tag {
  display: inline-block; font-size: 9px; margin: 1px 3px 1px 0;
  padding: 1px 4px; border-radius: 3px;
  background: rgba(0,0,0,0.5); backdrop-filter: blur(2px);
  border: 1px solid rgba(255,255,255,0.06);
  white-space: nowrap; line-height: 1.5;
}
.region-us { top: 12px; left: 16px; }
.region-europe { top: 12px; right: 16px; }
.region-asia { bottom: 70px; right: 16px; }
.region-commodity { bottom: 70px; left: 16px; }
.stat-card { background: rgba(17,18,20,0.7); backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 14px; }
.stat-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.stat-badge { font-size: 9px; padding: 2px 6px; border-radius: 4px; background: rgba(239,68,68,0.15); color: var(--red); text-transform: uppercase; letter-spacing: 1px; }
.stat-period { font-size: 10px; color: var(--muted); }
.stat-label { font-size: 11px; color: var(--muted); font-weight: 500; margin-bottom: 4px; }
.stat-number { font-size: 28px; font-weight: 200; font-family: 'JetBrains Mono', monospace; color: #fff; }
.stat-unit { font-size: 14px; color: var(--muted); }
.stat-sub { font-size: 10px; color: var(--muted); margin-top: 4px; }
.mt-4 { margin-top: 16px; }
.chain-card { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 8px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); }
.chain-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.chain-name { font-size: 11px; color: #fff; }
.chain-stress { font-size: 9px; color: var(--muted); }
.donut-row { display: flex; gap: 16px; justify-content: center; margin: 12px 0 8px; }
.donut-item { position: relative; width: 50px; height: 50px; }
.donut-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.donut-bg { fill: none; stroke: rgba(255,255,255,0.06); stroke-width: 3; }
.donut-fill { fill: none; stroke-width: 3; stroke-linecap: round; }
.donut-label { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 10px; font-family: 'JetBrains Mono'; color: #fff; }
.donut-legend { display: flex; gap: 12px; justify-content: center; font-size: 9px; color: var(--muted); }
.donut-legend i { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 4px; }
.region-bars { display: flex; flex-direction: column; gap: 5px; }
.region-bar { display: flex; align-items: center; gap: 6px; }
.region-name { font-size: 10px; color: var(--muted); width: 28px; flex-shrink: 0; }
.region-track { flex: 1; height: 4px; background: rgba(255,255,255,0.04); border-radius: 2px; overflow: hidden; }
.region-fill { height: 100%; border-radius: 2px; transition: width 0.6s; }
.region-val { font-size: 9px; font-family: 'JetBrains Mono'; color: var(--muted); width: 20px; text-align: right; }
</style>
