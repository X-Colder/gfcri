<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold">{{ t('industry.graphTitle') }}</h2>
      <div class="flex items-center gap-3">
        <select v-model="selectedIndustry" @change="buildGraph" class="bg-bg border border-border rounded-lg px-3 py-1.5 text-sm">
          <option v-for="ind in industryList" :key="ind.code" :value="ind.code">{{ ind.name }}</option>
        </select>
        <button @click="resetCamera" class="px-3 py-1.5 rounded-lg bg-card border border-border text-xs text-muted hover:text-white">{{ t('industry.resetCamera') }}</button>
      </div>
    </div>

    <!-- 3D Graph -->
    <div class="bg-[#060a0f] border border-border rounded-xl overflow-hidden relative" style="height: 620px">
      <div ref="graphContainer" class="w-full h-full"></div>

      <!-- Layer labels -->
      <div class="absolute top-4 left-4 bg-bg/90 border border-border rounded-lg p-2.5 backdrop-blur-sm">
        <p class="text-[10px] text-muted font-medium mb-1.5">{{ t('industry.layerHint') }}</p>
        <div class="space-y-1">
          <div v-for="layer in currentLayers" :key="layer.label" class="flex items-center gap-2">
            <div class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: layer.color }"></div>
            <span class="text-[10px]">{{ layer.label }}</span>
          </div>
        </div>
      </div>

      <!-- Clicked node panel -->
      <div v-if="selectedNode" class="absolute top-4 right-4 bg-bg/95 border border-border rounded-xl p-4 backdrop-blur-sm w-[240px]">
        <div class="flex items-center justify-between mb-2">
          <p class="text-sm font-bold">{{ selectedNode.fullLabel }}</p>
          <button @click="selectedNode = null" class="text-muted hover:text-white">×</button>
        </div>
        <p class="text-[10px] text-muted mb-2">{{ selectedNode.layerLabel }}</p>
        <div v-if="selectedNode.suppliesTo.length" class="mb-2">
          <p class="text-[10px] text-alert-green mb-1">{{ t('industry.suppliesTo') }} →</p>
          <div class="space-y-0.5">
            <p v-for="t in selectedNode.suppliesTo" :key="t" class="text-[11px] text-[#c9d1d9]">{{ tx(t) }}</p>
          </div>
        </div>
        <div v-if="selectedNode.buysFrom.length">
          <p class="text-[10px] text-accent mb-1">{{ t('industry.buysFrom') }} ←</p>
          <div class="space-y-0.5">
            <p v-for="t in selectedNode.buysFrom" :key="t" class="text-[11px] text-[#c9d1d9]">{{ tx(t) }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Flat chain view below -->
    <div class="bg-card border border-border rounded-xl p-5 overflow-x-auto">
      <div class="flex items-start gap-3 min-w-max">
        <template v-for="(layer, i) in currentLayers" :key="i">
          <div class="min-w-[160px] shrink-0">
            <p class="text-[10px] font-medium mb-2" :style="{ color: layer.color }">{{ layer.label }}</p>
            <div class="space-y-1.5">
              <div v-for="node in layer.nodes" :key="node.id" class="bg-bg border border-border/50 rounded-lg px-3 py-2">
                <span class="text-sm mr-1">{{ node.flag }}</span>
                <span class="text-xs">{{ node.economy }}</span>
                <p class="text-[10px] text-muted mt-0.5">{{ node.detail }}</p>
              </div>
            </div>
          </div>
          <div v-if="i < currentLayers.length - 1" class="flex items-center self-center pt-6">
            <svg class="w-5 h-5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import ForceGraph3D from '3d-force-graph'
import { useI18n } from '@/composables/useI18n'

const graphContainer = ref<HTMLElement | null>(null)
const selectedIndustry = ref('semiconductor')
const selectedNode = ref<any>(null)
const { t, tx, lang } = useI18n()
let graph: any = null

const ECON: Record<string, { name: string; flag: string }> = {
  US: { name: '美国', flag: '🇺🇸' }, CN: { name: '中国', flag: '🇨🇳' },
  EU: { name: '欧盟', flag: '🇪🇺' }, JP: { name: '日本', flag: '🇯🇵' },
  KR: { name: '韩国', flag: '🇰🇷' }, DE: { name: '德国', flag: '🇩🇪' },
  TW: { name: '台湾', flag: '🇹🇼' }, IN: { name: '印度', flag: '🇮🇳' },
  BR: { name: '巴西', flag: '🇧🇷' }, AU: { name: '澳大利亚', flag: '🇦🇺' },
  SA: { name: '沙特', flag: '🇸🇦' }, RU: { name: '俄罗斯', flag: '🇷🇺' },
  GB: { name: '英国', flag: '🇬🇧' }, FR: { name: '法国', flag: '🇫🇷' },
  IT: { name: '意大利', flag: '🇮🇹' }, CA: { name: '加拿大', flag: '🇨🇦' },
  ID: { name: '印尼', flag: '🇮🇩' }, ZA: { name: '南非', flag: '🇿🇦' },
  NL: { name: '荷兰', flag: '🇳🇱' }, CL: { name: '智利', flag: '🇨🇱' },
  MY: { name: '马来西亚', flag: '🇲🇾' }, AR: { name: '阿根廷', flag: '🇦🇷' },
}

interface ChainDef {
  name: string
  layers: { label: string; color: string; nodes: { eco: string; detail: string }[] }[]
  edges: [string, string][]  // [fromId, toId]
}

// Detailed supply chains with economy+role as nodes
const CHAINS: Record<string, ChainDef> = {
  semiconductor: {
    name: '半导体',
    layers: [
      { label: '基础材料', color: '#f0883e', nodes: [
        { eco: 'JP', detail: '硅晶圆/光刻胶' }, { eco: 'DE', detail: '特种气体/化学品' },
      ]},
      { label: '核心设备', color: '#db6d28', nodes: [
        { eco: 'NL', detail: 'ASML光刻机' }, { eco: 'US', detail: '应用材料/泛林' }, { eco: 'JP', detail: '东京电子/刻蚀' },
      ]},
      { label: '芯片设计', color: '#d29922', nodes: [
        { eco: 'US', detail: '英伟达/AMD/高通' }, { eco: 'TW', detail: '联发科' }, { eco: 'CN', detail: '海思/寒武纪' },
      ]},
      { label: '晶圆代工', color: '#2ea043', nodes: [
        { eco: 'TW', detail: '台积电(全球60%)' }, { eco: 'KR', detail: '三星晶圆厂' }, { eco: 'CN', detail: '中芯国际' },
      ]},
      { label: '封装测试', color: '#58a6ff', nodes: [
        { eco: 'TW', detail: '日月光/矽品' }, { eco: 'CN', detail: '长电科技' }, { eco: 'MY', detail: '封测代工' },
      ]},
      { label: '终端品牌', color: '#bc8cff', nodes: [
        { eco: 'US', detail: '苹果/特斯拉' }, { eco: 'CN', detail: '华为/小米' }, { eco: 'KR', detail: '三星电子' },
      ]},
    ],
    edges: [
      ['JP-0','NL-1'],['JP-0','TW-3'],['DE-0','NL-1'],['DE-0','TW-3'],
      ['NL-1','TW-3'],['NL-1','KR-3'],['NL-1','CN-3'],['US-1','TW-3'],['US-1','KR-3'],['JP-1','TW-3'],
      ['US-2','TW-3'],['US-2','KR-3'],['TW-2','TW-3'],['CN-2','CN-3'],
      ['TW-3','TW-4'],['TW-3','CN-4'],['KR-3','TW-4'],['CN-3','CN-4'],
      ['TW-4','US-5'],['TW-4','CN-5'],['CN-4','CN-5'],['KR-3','KR-5'],
    ],
  },
  iron_steel: {
    name: '钢铁',
    layers: [
      { label: '铁矿石开采', color: '#f0883e', nodes: [
        { eco: 'AU', detail: '力拓/必和必拓' }, { eco: 'BR', detail: '淡水河谷' }, { eco: 'ZA', detail: '南非矿业' },
      ]},
      { label: '焦煤供应', color: '#db6d28', nodes: [
        { eco: 'AU', detail: '炼焦煤出口' }, { eco: 'RU', detail: '煤炭出口' },
      ]},
      { label: '钢铁冶炼', color: '#d29922', nodes: [
        { eco: 'CN', detail: '宝武/河钢(全球53%)' }, { eco: 'IN', detail: '塔塔钢铁' }, { eco: 'JP', detail: '日本制铁' }, { eco: 'KR', detail: '浦项制铁' },
      ]},
      { label: '钢材加工', color: '#2ea043', nodes: [
        { eco: 'CN', detail: '热轧/冷轧/镀锌' }, { eco: 'JP', detail: '特种钢材' }, { eco: 'DE', detail: '蒂森克虏伯' },
      ]},
      { label: '终端制造', color: '#58a6ff', nodes: [
        { eco: 'CN', detail: '基建/地产' }, { eco: 'KR', detail: '造船/汽车' }, { eco: 'DE', detail: '汽车/机械' }, { eco: 'US', detail: '建筑/管道' },
      ]},
    ],
    edges: [
      ['AU-0','CN-2'],['AU-0','JP-2'],['AU-0','KR-2'],['BR-0','CN-2'],['ZA-0','CN-2'],
      ['AU-1','CN-2'],['AU-1','JP-2'],['RU-1','CN-2'],
      ['CN-2','CN-3'],['JP-2','JP-3'],['KR-2','KR-4'],
      ['CN-3','CN-4'],['CN-3','KR-4'],['JP-3','DE-4'],['JP-3','US-4'],['DE-3','DE-4'],
    ],
  },
  ev_battery: {
    name: '电动车电池',
    layers: [
      { label: '锂矿开采', color: '#f0883e', nodes: [
        { eco: 'AU', detail: '锂辉石矿' }, { eco: 'CL', detail: '盐湖提锂' }, { eco: 'AR', detail: '盐湖锂矿' },
      ]},
      { label: '镍钴矿产', color: '#db6d28', nodes: [
        { eco: 'ID', detail: '镍矿(全球第一)' }, { eco: 'AU', detail: '镍钴矿' },
      ]},
      { label: '正负极材料', color: '#d29922', nodes: [
        { eco: 'CN', detail: '杉杉/贝特瑞' }, { eco: 'KR', detail: 'L&F/EcoPro' }, { eco: 'JP', detail: '住友金属' },
      ]},
      { label: '电芯制造', color: '#2ea043', nodes: [
        { eco: 'CN', detail: '宁德时代/比亚迪' }, { eco: 'KR', detail: 'LG/三星SDI/SK' }, { eco: 'JP', detail: '松下' },
      ]},
      { label: '整车组装', color: '#58a6ff', nodes: [
        { eco: 'CN', detail: '比亚迪/蔚来' }, { eco: 'US', detail: '特斯拉' }, { eco: 'DE', detail: '大众/宝马' },
      ]},
      { label: '消费市场', color: '#bc8cff', nodes: [
        { eco: 'CN', detail: '最大市场' }, { eco: 'EU', detail: '政策驱动' }, { eco: 'US', detail: '增长市场' },
      ]},
    ],
    edges: [
      ['AU-0','CN-2'],['CL-0','CN-2'],['CL-0','KR-2'],['AR-0','CN-2'],
      ['ID-1','CN-2'],['ID-1','KR-2'],['AU-1','JP-2'],
      ['CN-2','CN-3'],['KR-2','KR-3'],['JP-2','JP-3'],
      ['CN-3','CN-4'],['CN-3','DE-4'],['KR-3','US-4'],['KR-3','DE-4'],['JP-3','US-4'],
      ['CN-4','CN-5'],['US-4','US-5'],['DE-4','EU-5'],
    ],
  },
  oil_gas: {
    name: '石油天然气',
    layers: [
      { label: '原油开采', color: '#f0883e', nodes: [
        { eco: 'SA', detail: 'OPEC核心(日产1000万桶)' }, { eco: 'RU', detail: '日产约900万桶' },
        { eco: 'US', detail: '页岩油(日产1300万桶)' }, { eco: 'CA', detail: '油砂/管道油' },
      ]},
      { label: '海运贸易', color: '#db6d28', nodes: [
        { eco: 'SA', detail: '→亚洲航线' }, { eco: 'RU', detail: '→中印航线' },
      ]},
      { label: '炼化加工', color: '#d29922', nodes: [
        { eco: 'CN', detail: '中石化/恒力(全球最大)' }, { eco: 'US', detail: '墨西哥湾炼厂' },
        { eco: 'IN', detail: '信实工业' }, { eco: 'KR', detail: 'SK/GS加德士' },
      ]},
      { label: '石化产品', color: '#2ea043', nodes: [
        { eco: 'CN', detail: '塑料/合成纤维' }, { eco: 'US', detail: '乙烯/丙烯' }, { eco: 'SA', detail: 'SABIC化工' },
      ]},
      { label: '终端消费', color: '#58a6ff', nodes: [
        { eco: 'CN', detail: '交通/工业' }, { eco: 'IN', detail: '交通/发电' }, { eco: 'EU', detail: '供暖/交通' }, { eco: 'JP', detail: '发电/工业' },
      ]},
    ],
    edges: [
      ['SA-0','CN-2'],['SA-0','IN-2'],['SA-0','KR-2'],['SA-0','JP-4'],
      ['RU-0','CN-2'],['RU-0','IN-2'],['US-0','US-2'],['CA-0','US-2'],
      ['CN-2','CN-3'],['US-2','US-3'],['SA-0','SA-3'],
      ['CN-3','CN-4'],['US-3','EU-4'],['IN-2','IN-4'],
    ],
  },
  ai_computing: {
    name: '人工智能',
    layers: [
      { label: 'GPU芯片', color: '#f0883e', nodes: [
        { eco: 'US', detail: '英伟达(设计)' }, { eco: 'TW', detail: '台积电(代工)' },
      ]},
      { label: '服务器/数据中心', color: '#db6d28', nodes: [
        { eco: 'US', detail: '戴尔/超微' }, { eco: 'TW', detail: '广达/鸿海' }, { eco: 'CN', detail: '浪潮/华为' },
      ]},
      { label: '云平台', color: '#d29922', nodes: [
        { eco: 'US', detail: 'AWS/Azure/GCP' }, { eco: 'CN', detail: '阿里云/华为云' },
      ]},
      { label: '大模型研发', color: '#2ea043', nodes: [
        { eco: 'US', detail: 'OpenAI/Anthropic/Meta' }, { eco: 'CN', detail: '字节/百度/智谱' }, { eco: 'FR', detail: 'Mistral' },
      ]},
      { label: '应用与消费', color: '#58a6ff', nodes: [
        { eco: 'US', detail: '企业SaaS' }, { eco: 'CN', detail: '互联网应用' }, { eco: 'IN', detail: 'IT外包/应用' }, { eco: 'JP', detail: '制造业AI' },
      ]},
    ],
    edges: [
      ['US-0','TW-0'],['TW-0','US-1'],['TW-0','TW-1'],['TW-0','CN-1'],
      ['US-1','US-2'],['TW-1','US-2'],['CN-1','CN-2'],
      ['US-2','US-3'],['CN-2','CN-3'],
      ['US-3','US-4'],['US-3','IN-4'],['US-3','JP-4'],['CN-3','CN-4'],
    ],
  },
  rare_earth: {
    name: '稀土',
    layers: [
      { label: '稀土矿开采', color: '#f0883e', nodes: [
        { eco: 'CN', detail: '全球70%产量' }, { eco: 'AU', detail: 'Lynas矿业' }, { eco: 'US', detail: 'MP Materials' },
      ]},
      { label: '分离冶炼', color: '#d29922', nodes: [
        { eco: 'CN', detail: '全球90%加工能力' },
      ]},
      { label: '磁材制造', color: '#2ea043', nodes: [
        { eco: 'CN', detail: '钕铁硼永磁' }, { eco: 'JP', detail: 'TDK/日立金属' },
      ]},
      { label: '终端应用', color: '#58a6ff', nodes: [
        { eco: 'CN', detail: '风电/电动车电机' }, { eco: 'DE', detail: '风电/工业电机' }, { eco: 'US', detail: '军工/电动车' }, { eco: 'JP', detail: '电子/汽车' },
      ]},
    ],
    edges: [
      ['CN-0','CN-1'],['AU-0','CN-1'],['US-0','CN-1'],
      ['CN-1','CN-2'],['CN-1','JP-2'],
      ['CN-2','CN-3'],['CN-2','DE-3'],['CN-2','US-3'],['JP-2','JP-3'],
    ],
  },
}

const industryList = computed(() =>
  Object.entries(CHAINS).map(([code, v]) => ({ code, name: tx(v.name) }))
)

const currentLayers = computed(() => {
  const chain = CHAINS[selectedIndustry.value]
  if (!chain) return []
  return chain.layers.map((layer, li) => ({
    ...layer,
    label: tx(layer.label),
    nodes: layer.nodes.map((n) => ({
      id: `${n.eco}-${li}`,
      economy: tx(ECON[n.eco]?.name || n.eco),
      flag: ECON[n.eco]?.flag || '🌐',
      detail: tx(n.detail),
    })),
  }))
})

onMounted(() => { buildGraph() })
onBeforeUnmount(() => { if (graph) graph._destructor?.() })

watch(lang, () => {
  selectedNode.value = null
  buildGraph()
})

function buildGraph() {
  if (!graphContainer.value) return
  if (graph) { graph._destructor?.(); graph = null }

  const chain = CHAINS[selectedIndustry.value]
  if (!chain) return

  const nodes: any[] = []
  const nodeMap: Record<string, any> = {}

  chain.layers.forEach((layer, li) => {
    const count = layer.nodes.length
    layer.nodes.forEach((n, ni) => {
      const id = `${n.eco}-${li}`
      const meta = ECON[n.eco] || { name: n.eco, flag: '🌐' }
      const xSpread = (ni - (count - 1) / 2) * 50
      const node = {
        id,
        economy: tx(meta.name),
        flag: meta.flag,
        detail: tx(n.detail),
        layerLabel: tx(layer.label),
        layerColor: layer.color,
        fullLabel: `${meta.flag} ${tx(meta.name)} · ${tx(n.detail)}`,
        fx: xSpread,
        fy: -(li * 55),
        fz: (Math.random() - 0.5) * 20,
      }
      nodes.push(node)
      nodeMap[id] = node
    })
  })

  const links = chain.edges
    .filter(([s, t]) => nodeMap[s] && nodeMap[t])
    .map(([s, t]) => ({ source: s, target: t }))

  graph = (ForceGraph3D as any)()(graphContainer.value)
    .backgroundColor('#060a0f')
    .graphData({ nodes, links })
    .nodeLabel((node: any) =>
      `<div style="background:#060a0fee;border:1px solid ${node.layerColor};border-radius:8px;padding:8px 12px;max-width:200px">
        <div style="font-size:14px;margin-bottom:2px">${node.flag} <b style="color:#e6edf3">${node.economy}</b></div>
        <div style="font-size:11px;color:${node.layerColor}">${node.detail}</div>
        <div style="font-size:10px;color:#627588;margin-top:3px">${node.layerLabel}</div>
      </div>`)
    .nodeColor((node: any) => node.layerColor)
    .nodeVal(7)
    .nodeOpacity(0.95)
    .nodeResolution(20)
    .linkWidth(2.5)
    .linkColor(() => '#ffffff25')
    .linkOpacity(0.6)
    .linkDirectionalArrowLength(5)
    .linkDirectionalArrowRelPos(0.85)
    .linkDirectionalArrowColor(() => '#ffffff50')
    .linkDirectionalParticles(3)
    .linkDirectionalParticleWidth(2.5)
    .linkDirectionalParticleColor(() => '#58a6ff90')
    .linkDirectionalParticleSpeed(0.006)
    .linkCurvature(0.2)
    .cooldownTicks(0)
    .onNodeClick((node: any) => {
      if (!node) return
      const suppliesTo = links
        .filter(l => (typeof l.source === 'object' ? (l.source as any).id : l.source) === node.id)
        .map(l => { const tid = typeof l.target === 'object' ? (l.target as any).id : l.target; return nodeMap[tid]?.fullLabel || tid })
      const buysFrom = links
        .filter(l => (typeof l.target === 'object' ? (l.target as any).id : l.target) === node.id)
        .map(l => { const sid = typeof l.source === 'object' ? (l.source as any).id : l.source; return nodeMap[sid]?.fullLabel || sid })
      selectedNode.value = { ...node, suppliesTo, buysFrom }

      const d = 80
      const r = 1 + d / Math.hypot(node.x||1, node.y||1, node.z||1)
      graph.cameraPosition({ x: (node.x||0)*r, y: (node.y||0)*r, z: (node.z||0)*r }, { x: node.x, y: node.y, z: node.z }, 600)
    })

  const totalLayers = chain.layers.length
  setTimeout(() => {
    graph.cameraPosition({ x: 60, y: -(totalLayers * 25) + 40, z: 220 }, { x: 0, y: -(totalLayers * 25), z: 0 }, 0)
  }, 50)
}

function resetCamera() {
  const chain = CHAINS[selectedIndustry.value]
  if (!chain || !graph) return
  const totalLayers = chain.layers.length
  graph.cameraPosition({ x: 60, y: -(totalLayers * 25) + 40, z: 220 }, { x: 0, y: -(totalLayers * 25), z: 0 }, 600)
}
</script>
