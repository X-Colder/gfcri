<template>
  <section class="terminal-section trade-atlas-section p-5">
    <div class="trade-atlas-header">
      <div>
        <p class="terminal-kicker">Global Trade Risk Atlas</p>
        <h2 class="mt-1 text-base font-medium text-white">全球贸易风险图谱</h2>
        <p class="terminal-copy mt-2 max-w-4xl">
          将主要经济体的贸易流、转口路径和风险触发器组织成可下钻的机构视图，默认突出当前最需要关注的贸易走廊和风险节点。
        </p>
      </div>
      <div class="trade-atlas-metrics">
        <div class="terminal-metric">
          <span>高风险走廊</span>
          <strong>{{ highRiskCorridorCount }}</strong>
        </div>
        <div class="terminal-metric">
          <span>核心节点</span>
          <strong>{{ tradeNodes.length }}</strong>
        </div>
        <div class="terminal-metric">
          <span>数据模式</span>
          <strong>v0.1</strong>
        </div>
      </div>
    </div>

    <div class="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_360px]">
      <div class="space-y-4">
        <div class="trade-control-row">
          <div class="segmented-control" aria-label="贸易风险视图">
            <button
              v-for="view in viewModes"
              :key="view.id"
              type="button"
              :class="{ active: activeView === view.id }"
              @click="activeView = view.id"
            >
              {{ view.label }}
            </button>
          </div>
          <div class="segmented-control risk-filter" aria-label="风险类型过滤">
            <button
              v-for="risk in riskFilters"
              :key="risk.id"
              type="button"
              :class="{ active: activeRisk === risk.id }"
              @click="activeRisk = risk.id"
            >
              <span :style="{ background: risk.color }"></span>
              {{ risk.label }}
            </button>
          </div>
        </div>

        <div v-if="activeView === 'map'" class="trade-map-shell">
          <svg class="trade-map" viewBox="0 0 1000 560" role="img" aria-label="全球贸易风险网络地图">
            <defs>
              <marker id="tradeArrowRed" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="#ef4444" />
              </marker>
              <marker id="tradeArrowAmber" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="#f59e0b" />
              </marker>
              <marker id="tradeArrowBlue" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="#58a6ff" />
              </marker>
            </defs>
            <path
              v-for="corridor in filteredCorridors"
              :key="corridor.id"
              class="trade-corridor-line"
              :class="{ selected: selectedCorridor?.id === corridor.id }"
              :d="corridorPath(corridor)"
              :stroke="riskColor(corridor.risk)"
              :stroke-width="lineWidth(corridor)"
              :stroke-dasharray="corridor.reroute ? '10 9' : undefined"
              :marker-end="arrowMarker(corridor)"
              @click="selectCorridor(corridor.id)"
            />
            <path
              v-for="corridor in mutedCorridors"
              :key="`muted-${corridor.id}`"
              class="trade-corridor-line muted"
              :d="corridorPath(corridor)"
              :stroke="riskColor(corridor.risk)"
              :stroke-width="lineWidth(corridor)"
              :stroke-dasharray="corridor.reroute ? '10 9' : undefined"
            />
          </svg>

          <button
            v-for="node in tradeNodes"
            :key="node.id"
            type="button"
            class="trade-node"
            :class="{ selected: selectedNode?.id === node.id, dimmed: !nodeIsActive(node.id) }"
            :style="{ left: `${node.x / 10}%`, top: `${node.y / 5.6}%` }"
            @click="selectNode(node.id)"
          >
            <span class="node-risk-ring" :style="{ borderColor: riskColor(node.risk) }"></span>
            <span class="node-name">{{ node.short }}</span>
            <span class="node-score" :style="{ color: riskColor(node.risk) }">{{ node.risk }}</span>
          </button>

          <div class="map-legend">
            <span><i class="solid-line"></i>直接贸易流</span>
            <span><i class="dashed-line"></i>转口/重路由</span>
            <span><i class="node-dot"></i>节点外圈代表风险强度</span>
          </div>
        </div>

        <div v-else-if="activeView === 'flow'" class="flow-view">
          <div v-for="stage in flowStages" :key="stage.id" class="flow-stage">
            <p class="flow-stage-label">{{ stage.label }}</p>
            <button
              v-for="nodeId in stage.nodes"
              :key="nodeId"
              type="button"
              class="flow-node"
              @click="selectNode(nodeId)"
            >
              <span>{{ nodeById(nodeId)?.name }}</span>
              <strong :style="{ color: riskColor(nodeById(nodeId)?.risk || 0) }">{{ nodeById(nodeId)?.risk }}</strong>
            </button>
          </div>
          <div class="flow-summary">
            <article v-for="corridor in filteredRankedCorridors.slice(0, 6)" :key="corridor.id" class="flow-corridor" @click="selectCorridor(corridor.id)">
              <div>
                <p>{{ corridor.label }}</p>
                <span>{{ corridor.goods }}</span>
              </div>
              <strong :style="{ color: riskColor(corridor.risk) }">{{ corridor.risk }}</strong>
            </article>
          </div>
        </div>

        <div v-else-if="activeView === 'shock'" class="shock-view">
          <div class="shock-scenarios">
            <button
              v-for="scenario in shockScenarios"
              :key="scenario.id"
              type="button"
              :class="{ active: activeScenario === scenario.id }"
              @click="activeScenario = scenario.id"
            >
              <span>{{ scenario.label }}</span>
              <strong :style="{ color: riskColor(scenario.risk) }">{{ scenario.risk }}</strong>
            </button>
          </div>
          <div class="shock-detail">
            <div>
              <p class="text-[10px] uppercase tracking-wide text-[var(--muted)]">Transmission Path</p>
              <h3 class="mt-1 text-sm font-medium text-white">{{ selectedScenario?.title }}</h3>
              <p class="mt-2 text-xs leading-relaxed text-[var(--muted)]">{{ selectedScenario?.summary }}</p>
            </div>
            <div class="shock-steps">
              <div v-for="(step, index) in selectedScenario?.steps || []" :key="step" class="shock-step">
                <span>{{ index + 1 }}</span>
                <p>{{ step }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="evidence-view">
          <article v-for="item in evidenceBlocks" :key="item.title" class="evidence-block">
            <p class="text-[10px] uppercase tracking-wide text-[var(--muted)]">{{ item.kicker }}</p>
            <h3 class="mt-1 text-sm font-medium text-white">{{ item.title }}</h3>
            <p class="mt-2 text-xs leading-relaxed text-[var(--muted)]">{{ item.body }}</p>
          </article>
        </div>
      </div>

      <aside class="trade-side-panel">
        <div class="risk-judgment">
          <p class="text-[10px] uppercase tracking-wide text-[var(--muted)]">Key Judgment</p>
          <h3 class="mt-1 text-sm font-medium text-white">贸易风险正在从单点摩擦转向路径重构</h3>
          <p class="mt-2 text-xs leading-relaxed text-[var(--muted)]">
            美国需求、中国制造、东亚半导体和 ASEAN/墨西哥转口链条共同决定风险传导强度。当前最需要关注关税、AI硬件周期和能源航运三类触发器。
          </p>
        </div>

        <div class="detail-panel">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-[10px] uppercase tracking-wide text-[var(--muted)]">{{ selectedNode ? 'Node Detail' : 'Corridor Detail' }}</p>
              <h3 class="mt-1 text-sm font-medium text-white">{{ detailTitle }}</h3>
            </div>
            <strong class="font-mono text-2xl font-medium" :style="{ color: riskColor(detailRisk) }">{{ detailRisk }}</strong>
          </div>
          <p class="mt-3 text-xs leading-relaxed text-[var(--muted)]">{{ detailSummary }}</p>
          <div class="mt-4 flex flex-wrap gap-1.5">
            <span v-for="tag in detailTags" :key="tag" class="risk-tag">{{ riskLabel(tag) }}</span>
          </div>
          <div class="mt-4 space-y-3">
            <div>
              <p class="detail-label">主要暴露</p>
              <p class="detail-text">{{ detailExposure }}</p>
            </div>
            <div>
              <p class="detail-label">下一步观察</p>
              <p class="detail-text">{{ detailWatch }}</p>
            </div>
          </div>
        </div>

        <div class="top-corridors">
          <p class="text-[10px] uppercase tracking-wide text-[var(--muted)]">Top Risk Corridors</p>
          <button
            v-for="corridor in filteredRankedCorridors.slice(0, 5)"
            :key="corridor.id"
            type="button"
            class="top-corridor"
            :class="{ active: selectedCorridor?.id === corridor.id }"
            @click="selectCorridor(corridor.id)"
          >
            <span>
              <strong>{{ corridor.label }}</strong>
              <em>{{ corridor.trigger }}</em>
            </span>
            <b :style="{ color: riskColor(corridor.risk) }">{{ corridor.risk }}</b>
          </button>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

type ViewKey = 'map' | 'flow' | 'shock' | 'evidence'
type RiskKey = 'all' | 'tariff' | 'shipping' | 'energy' | 'fx' | 'demand' | 'tech' | 'ai' | 'commodity'

interface TradeNode {
  id: string
  name: string
  short: string
  role: string
  x: number
  y: number
  risk: number
  importance: number
  tags: RiskKey[]
  summary: string
  exposure: string
  watch: string
}

interface TradeCorridor {
  id: string
  from: string
  to: string
  label: string
  goods: string
  risk: number
  volume: number
  tags: RiskKey[]
  trigger: string
  summary: string
  exposure: string
  watch: string
  reroute?: boolean
}

interface ShockScenario {
  id: string
  label: string
  title: string
  risk: number
  summary: string
  steps: string[]
}

const viewModes: Array<{ id: ViewKey; label: string }> = [
  { id: 'map', label: '地图' },
  { id: 'flow', label: '流向' },
  { id: 'shock', label: '冲击' },
  { id: 'evidence', label: '证据' },
]

const riskFilters: Array<{ id: RiskKey; label: string; color: string }> = [
  { id: 'all', label: '全部', color: '#58a6ff' },
  { id: 'tariff', label: '关税', color: '#ef4444' },
  { id: 'shipping', label: '航运', color: '#f97316' },
  { id: 'energy', label: '能源', color: '#f59e0b' },
  { id: 'fx', label: '汇率', color: '#22c55e' },
  { id: 'demand', label: '需求', color: '#38bdf8' },
  { id: 'tech', label: '技术管制', color: '#a78bfa' },
  { id: 'ai', label: 'AI硬件', color: '#14b8a6' },
  { id: 'commodity', label: '大宗商品', color: '#eab308' },
]

const tradeNodes: TradeNode[] = [
  {
    id: 'us',
    name: '美国',
    short: '美国',
    role: '终端需求 / 关税规则制定者',
    x: 160,
    y: 220,
    risk: 86,
    importance: 98,
    tags: ['tariff', 'demand', 'tech'],
    summary: '美国仍是全球制造品和高端设备的关键终端需求端，也是关税、原产地审查和技术管制的主要变量来源。',
    exposure: '进口依赖分散到墨西哥、加拿大、中国、越南、台湾和韩国，但消费周期与政策冲击会同步影响全球出口链。',
    watch: '美国关税公告、零售销售、库存周期、科技管制清单和原产地审查。'
  },
  {
    id: 'mexico',
    name: '墨西哥',
    short: '墨西哥',
    role: '近岸制造 / 美国入口',
    x: 135,
    y: 320,
    risk: 68,
    importance: 74,
    tags: ['tariff', 'demand'],
    summary: '墨西哥是美国近岸制造的主要承接地，受益于供应链重构，也暴露于美国对转口和原产地规则的追溯。',
    exposure: '汽车、机械、电子组装和跨境供应链对美国终端需求高度敏感。',
    watch: 'USMCA 原产地规则、汽车零部件审查和对美出口异常增速。'
  },
  {
    id: 'latam',
    name: '巴西 / 拉美',
    short: '拉美',
    role: '农产品 / 金属资源',
    x: 260,
    y: 430,
    risk: 54,
    importance: 64,
    tags: ['commodity', 'fx'],
    summary: '拉美向中国、欧盟和美国提供农产品、矿产和能源，是资源价格与美元融资压力的交汇点。',
    exposure: '大豆、铁矿、铜、原油和食品贸易受中国工业周期、美元和气候扰动影响。',
    watch: '中国进口量、美元指数、铜价、粮价和本币汇率。'
  },
  {
    id: 'eu',
    name: '欧盟 / 德国',
    short: '欧盟',
    role: '高端工业 / 夹层市场',
    x: 470,
    y: 175,
    risk: 74,
    importance: 88,
    tags: ['tariff', 'energy', 'demand'],
    summary: '欧盟出口端依赖美国高附加值需求，进口端依赖中国制造，处在中美贸易重构和能源成本之间。',
    exposure: '汽车、机械、化工和奢侈品出口受美国需求影响；电气机械和消费品进口受中国供应链影响。',
    watch: '欧盟反补贴调查、对美出口订单、天然气价格和德国工业订单。'
  },
  {
    id: 'middle_east',
    name: '中东',
    short: '中东',
    role: '能源 / 航运咽喉',
    x: 560,
    y: 315,
    risk: 78,
    importance: 82,
    tags: ['energy', 'shipping'],
    summary: '中东是油气供给和关键航运通道的风险源，冲击会通过能源价格、保险和运费传导到制造链。',
    exposure: '原油、LNG、化工原料和霍尔木兹/红海航运风险影响欧洲与亚洲进口成本。',
    watch: '油价、LNG、海运保险费、红海绕航比例和霍尔木兹风险事件。'
  },
  {
    id: 'africa',
    name: '非洲',
    short: '非洲',
    role: '矿产 / 新兴需求',
    x: 505,
    y: 410,
    risk: 58,
    importance: 56,
    tags: ['commodity', 'fx'],
    summary: '非洲同时是关键矿产供应地和新兴市场需求端，受美元融资、食品能源价格和中国投资周期影响。',
    exposure: '铜、钴、铁矿、能源和基建进口形成双向风险。',
    watch: '关键矿产出口、主权利差、食品能源进口成本和美元融资条件。'
  },
  {
    id: 'india',
    name: '印度',
    short: '印度',
    role: '替代制造 / 内需市场',
    x: 620,
    y: 395,
    risk: 61,
    importance: 66,
    tags: ['tariff', 'energy', 'demand'],
    summary: '印度受益于部分供应链转移，但能源进口依赖、政策保护和基础设施约束限制承接速度。',
    exposure: '电子组装、药品、纺织和能源进口对政策与油价敏感。',
    watch: '电子出口、原油进口成本、卢比汇率和对美贸易政策。'
  },
  {
    id: 'china',
    name: '中国',
    short: '中国',
    role: '制造核心 / 出口升级',
    x: 690,
    y: 265,
    risk: 82,
    importance: 96,
    tags: ['tariff', 'tech', 'ai', 'commodity'],
    summary: '中国仍是全球制造核心，机电、高技术、AI硬件和绿色产品出口增强，同时面临欧美关税和反补贴压力。',
    exposure: '对欧美终端需求、东亚零部件、资源进口和 ASEAN/墨西哥重路由链条都有系统性影响。',
    watch: '7-8月出口回落幅度、机电/高技术出口、欧美关税动作和 AI 硬件订单。'
  },
  {
    id: 'east_asia',
    name: '台湾 / 韩国 / 日本',
    short: '东亚',
    role: '半导体 / 设备链',
    x: 795,
    y: 235,
    risk: 80,
    importance: 90,
    tags: ['ai', 'tech', 'fx'],
    summary: '东亚半导体和设备链是 AI 硬件周期的核心节点，也暴露于技术管制、库存周期和汇率波动。',
    exposure: '芯片、存储、半导体设备、汽车零部件和精密机械与全球资本开支周期高度同步。',
    watch: '台湾与韩国半导体出口、存储价格、日本设备订单和韩元/日元汇率。'
  },
  {
    id: 'asean',
    name: 'ASEAN',
    short: 'ASEAN',
    role: '转口 / 组装承接',
    x: 720,
    y: 385,
    risk: 72,
    importance: 76,
    tags: ['tariff', 'shipping', 'tech'],
    summary: 'ASEAN 是供应链转移和转口的重要承接地，但出口异常高增容易被美国和欧盟纳入原产地审查。',
    exposure: '电子、家具、纺织、机械组装和中国零部件输入形成高弹性的贸易绕行路径。',
    watch: '越南/泰国/马来西亚对美出口增速、中国零部件进口和原产地审查新闻。'
  },
  {
    id: 'australia',
    name: '澳洲',
    short: '澳洲',
    role: '矿石 / 能源',
    x: 830,
    y: 470,
    risk: 52,
    importance: 62,
    tags: ['commodity', 'energy'],
    summary: '澳洲是铁矿、煤炭、LNG 和农业品供应地，风险主要通过中国工业周期和能源价格传导。',
    exposure: '资源出口对中国地产/工业周期、全球钢铁需求和 LNG 价格敏感。',
    watch: '铁矿石价格、中国钢材需求、LNG 价格和澳元。'
  },
]

const tradeCorridors: TradeCorridor[] = [
  {
    id: 'china-us',
    from: 'china',
    to: 'us',
    label: '中国 → 美国',
    goods: '电子、机械、消费品、汽车零部件',
    risk: 88,
    volume: 95,
    tags: ['tariff', 'demand', 'tech'],
    trigger: '关税与原产地审查',
    summary: '最核心的贸易摩擦走廊。直接出口受关税影响，间接路径则推高 ASEAN/墨西哥转口审查风险。',
    exposure: '美国消费和科技管制决定需求弹性，中国制造链决定全球供给弹性。',
    watch: '美国关税窗口、提前出货后回落、对越南/墨西哥转口审查。'
  },
  {
    id: 'china-eu',
    from: 'china',
    to: 'eu',
    label: '中国 → 欧盟',
    goods: '电气机械、汽车、光伏、消费品',
    risk: 79,
    volume: 82,
    tags: ['tariff', 'demand', 'tech'],
    trigger: '反补贴与产业保护',
    summary: '欧盟需要中国供应链，但在汽车、绿色产品和高端制造上面临本土产业压力。',
    exposure: '欧盟进口成本、反补贴调查和德国工业竞争力形成拉扯。',
    watch: '欧盟反补贴调查、汽车关税、德国工业订单和港口库存。'
  },
  {
    id: 'eastasia-china',
    from: 'east_asia',
    to: 'china',
    label: '东亚 → 中国',
    goods: '半导体、设备、存储、精密零部件',
    risk: 84,
    volume: 88,
    tags: ['ai', 'tech', 'fx'],
    trigger: 'AI硬件周期集中',
    summary: 'AI资本开支上行时强化贸易，若订单放缓会同步影响中国组装、韩国/台湾出口和日本设备链。',
    exposure: '半导体出口、设备订单和存储价格是该链条的领先信号。',
    watch: 'HBM/存储价格、台湾出口订单、韩国芯片出口和日本设备出货。'
  },
  {
    id: 'china-asean-us',
    from: 'china',
    to: 'asean',
    label: '中国 → ASEAN → 美国',
    goods: '零部件、电子组装、家具、纺织',
    risk: 76,
    volume: 72,
    tags: ['tariff', 'shipping', 'tech'],
    trigger: '转口路径审查',
    summary: '贸易不是消失，而是重路由。该路径越活跃，越容易触发原产地规则和反规避调查。',
    exposure: '中国零部件输入和 ASEAN 对美出口的剪刀差是风险识别重点。',
    watch: 'ASEAN 对美出口异常高增、从中国进口中间品增速、美国反规避调查。',
    reroute: true
  },
  {
    id: 'mexico-us',
    from: 'mexico',
    to: 'us',
    label: '墨西哥 → 美国',
    goods: '汽车、机械、电子、工业品',
    risk: 71,
    volume: 86,
    tags: ['tariff', 'demand'],
    trigger: '近岸制造拥挤',
    summary: '墨西哥受益于近岸制造，但也成为美国规则追溯和供应链拥挤的焦点。',
    exposure: '汽车与工业链条对美国库存周期和 USMCA 规则敏感。',
    watch: '汽车零部件原产地、边境物流、美国制造订单。'
  },
  {
    id: 'eu-us',
    from: 'eu',
    to: 'us',
    label: '欧盟 → 美国',
    goods: '汽车、机械、药品、化工',
    risk: 73,
    volume: 80,
    tags: ['tariff', 'demand'],
    trigger: '美国需求与关税政策',
    summary: '欧盟出口端高度依赖美国高附加值需求，若美国关税升级，欧洲制造利润率会被压缩。',
    exposure: '德国汽车、机械和药品出口是主要敏感点。',
    watch: '美国进口关税、欧元汇率、德国出口订单。'
  },
  {
    id: 'middleeast-eu',
    from: 'middle_east',
    to: 'eu',
    label: '中东 → 欧盟',
    goods: '原油、LNG、化工原料',
    risk: 77,
    volume: 66,
    tags: ['energy', 'shipping'],
    trigger: '能源与航运成本',
    summary: '能源和航运冲击会直接抬升欧洲制造成本，并影响通胀回落路径。',
    exposure: '油气价格、保险费和绕航成本共同决定输入型通胀。',
    watch: '布油、TTF天然气、红海绕航比例、海运保险费。'
  },
  {
    id: 'australia-china',
    from: 'australia',
    to: 'china',
    label: '澳洲 → 中国',
    goods: '铁矿、LNG、煤炭、农产品',
    risk: 57,
    volume: 70,
    tags: ['commodity', 'energy'],
    trigger: '中国工业周期',
    summary: '该走廊更多反映中国工业需求和资源价格，而不是贸易摩擦本身。',
    exposure: '铁矿石与 LNG 对中国工业、地产和能源需求变化敏感。',
    watch: '铁矿、钢材开工、LNG价格、中国进口量。'
  },
  {
    id: 'latam-china',
    from: 'latam',
    to: 'china',
    label: '拉美 → 中国',
    goods: '大豆、铁矿、铜、原油',
    risk: 62,
    volume: 64,
    tags: ['commodity', 'fx'],
    trigger: '资源价格与美元',
    summary: '资源贸易强度受中国需求、美元和气候扰动影响，新兴市场货币会放大冲击。',
    exposure: '铜、粮食和能源价格会向新兴市场外部压力传导。',
    watch: '铜价、粮价、美元指数、巴西雷亚尔和中国进口量。'
  },
]

const shockScenarios: ShockScenario[] = [
  {
    id: 'us-tariff',
    label: '美国关税冲击',
    title: '美国关税上调与原产地追溯',
    risk: 88,
    summary: '冲击先压缩中国直达美国的出口利润，再推高 ASEAN/墨西哥转口，最终触发更广泛的反规避审查。',
    steps: ['中国直达美国订单提前出货后回落', 'ASEAN/墨西哥承接转口和组装需求', '原产地审查覆盖中间品来源', '全球制造利润率与库存周转承压']
  },
  {
    id: 'ai-slowdown',
    label: 'AI硬件降温',
    title: 'AI资本开支放缓',
    risk: 84,
    summary: '若云厂商资本开支降温，东亚半导体、中国组装和美国科技设备需求会同步收缩。',
    steps: ['芯片和存储订单增速下滑', '东亚出口与设备订单走弱', '中国高技术出口降温', '铜、能源和航运需求同步回落']
  },
  {
    id: 'shipping-energy',
    label: '能源航运扰动',
    title: '中东航运与能源成本上行',
    risk: 78,
    summary: '能源和海运冲击会以成本形式穿透到欧洲、亚洲制造链，并重新推高通胀预期。',
    steps: ['红海/霍尔木兹风险抬升保险费', '油气与化工原料价格上行', '欧洲和亚洲进口成本上升', '终端需求和利润率同时受压']
  },
]

const evidenceBlocks = [
  {
    kicker: 'Source Tier',
    title: '当前版本使用结构化静态配置',
    body: 'v0.1.1 先提供交互和审计框架，节点和走廊来自公开贸易结构、政策风险和 GFCRI 现有传导链逻辑的综合映射；后续版本应接入海关、WTO、UNCTAD、Eurostat、US Census 等时间序列。'
  },
  {
    kicker: 'Formula Receipt',
    title: '风险分数用于排序，不是投资建议',
    body: '节点和走廊风险分数由系统重要性、近期政策风险、贸易集中度、替代路径脆弱性和对 GFCRI 子指数的传导强度综合给出，当前不作为交易信号。'
  },
  {
    kicker: 'Data Limits',
    title: '转口和原产地风险需要进一步验证',
    body: '转口路径使用虚线展示，表示需要以中间品进口、对美出口、行业订单和原产地审查新闻进行交叉验证。'
  },
  {
    kicker: 'Disclaimer',
    title: '风险监测用途',
    body: '该模块用于宏观贸易风险监测和机构研究沟通，不构成投资建议、贸易建议、法律建议或任何证券买卖建议。'
  },
]

const flowStages = [
  { id: 'resource', label: '资源 / 零部件', nodes: ['australia', 'latam', 'middle_east', 'east_asia'] },
  { id: 'manufacturing', label: '制造 / 转口', nodes: ['china', 'asean', 'mexico', 'india'] },
  { id: 'demand', label: '终端需求 / 高端工业', nodes: ['us', 'eu'] },
]

const activeView = ref<ViewKey>('map')
const activeRisk = ref<RiskKey>('all')
const activeScenario = ref('us-tariff')
const selectedCorridorId = ref('china-us')
const selectedNodeId = ref<string | null>(null)

const selectedCorridor = computed(() => tradeCorridors.find((item) => item.id === selectedCorridorId.value) || tradeCorridors[0])
const selectedNode = computed(() => selectedNodeId.value ? tradeNodes.find((item) => item.id === selectedNodeId.value) || null : null)
const selectedScenario = computed(() => shockScenarios.find((item) => item.id === activeScenario.value) || shockScenarios[0])
const filteredCorridors = computed(() =>
  tradeCorridors.filter((item) => activeRisk.value === 'all' || item.tags.includes(activeRisk.value))
)
const mutedCorridors = computed(() =>
  activeRisk.value === 'all' ? [] : tradeCorridors.filter((item) => !item.tags.includes(activeRisk.value))
)
const filteredRankedCorridors = computed(() => [...filteredCorridors.value].sort((a, b) => b.risk - a.risk))
const highRiskCorridorCount = computed(() => tradeCorridors.filter((item) => item.risk >= 75).length)
const detailTitle = computed(() => selectedNode.value ? selectedNode.value.name : selectedCorridor.value.label)
const detailRisk = computed(() => selectedNode.value ? selectedNode.value.risk : selectedCorridor.value.risk)
const detailSummary = computed(() => selectedNode.value ? selectedNode.value.summary : selectedCorridor.value.summary)
const detailExposure = computed(() => selectedNode.value ? selectedNode.value.exposure : selectedCorridor.value.exposure)
const detailWatch = computed(() => selectedNode.value ? selectedNode.value.watch : selectedCorridor.value.watch)
const detailTags = computed(() => selectedNode.value ? selectedNode.value.tags : selectedCorridor.value.tags)

function nodeById(id: string): TradeNode | undefined {
  return tradeNodes.find((node) => node.id === id)
}

function corridorPath(corridor: TradeCorridor): string {
  const from = nodeById(corridor.from)
  const to = nodeById(corridor.to)
  if (!from || !to) return ''
  const midX = (from.x + to.x) / 2
  const curvature = corridor.reroute ? 70 : 36
  const direction = from.y > to.y ? -1 : 1
  return `M ${from.x} ${from.y} C ${midX} ${from.y + curvature * direction}, ${midX} ${to.y - curvature * direction}, ${to.x} ${to.y}`
}

function selectCorridor(id: string) {
  selectedCorridorId.value = id
  selectedNodeId.value = null
}

function selectNode(id: string) {
  selectedNodeId.value = id
}

function lineWidth(corridor: TradeCorridor): number {
  return 2 + corridor.volume / 22
}

function riskColor(value: number): string {
  if (value >= 80) return '#ef4444'
  if (value >= 70) return '#f97316'
  if (value >= 58) return '#f59e0b'
  return '#34d399'
}

function arrowMarker(corridor: TradeCorridor): string {
  if (corridor.risk >= 80) return 'url(#tradeArrowRed)'
  if (corridor.risk >= 58) return 'url(#tradeArrowAmber)'
  return 'url(#tradeArrowBlue)'
}

function nodeIsActive(id: string): boolean {
  if (activeRisk.value === 'all') return true
  return filteredCorridors.value.some((corridor) => corridor.from === id || corridor.to === id)
}

function riskLabel(key: RiskKey): string {
  return riskFilters.find((item) => item.id === key)?.label || key
}
</script>

<style scoped>
.trade-atlas-section {
  overflow: hidden;
}

.trade-atlas-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
  gap: 18px;
  align-items: start;
}

.trade-atlas-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.trade-control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
}

.segmented-control {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.018);
}

.segmented-control button {
  display: inline-flex;
  min-height: 30px;
  align-items: center;
  gap: 6px;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 11px;
  color: var(--muted);
  transition: color 0.16s ease, background 0.16s ease;
}

.segmented-control button.active {
  background: rgba(88, 166, 255, 0.13);
  color: #fff;
}

.risk-filter button span {
  width: 7px;
  height: 7px;
  border-radius: 999px;
}

.trade-map-shell {
  position: relative;
  min-height: 520px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 8px;
  background:
    linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px),
    radial-gradient(circle at 65% 42%, rgba(20, 184, 166, 0.12), transparent 34%),
    radial-gradient(circle at 26% 38%, rgba(239, 68, 68, 0.10), transparent 32%),
    #070b12;
  background-size: 40px 40px, 40px 40px, auto, auto, auto;
}

.trade-map {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.trade-corridor-line {
  fill: none;
  cursor: pointer;
  opacity: 0.74;
  stroke-linecap: round;
  transition: opacity 0.16s ease, stroke-width 0.16s ease;
}

.trade-corridor-line:hover,
.trade-corridor-line.selected {
  opacity: 1;
  stroke-width: 7;
}

.trade-corridor-line.muted {
  pointer-events: none;
  opacity: 0.11;
}

.trade-node {
  position: absolute;
  display: grid;
  width: 82px;
  min-height: 56px;
  transform: translate(-50%, -50%);
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 8px;
  background: rgba(7, 11, 18, 0.84);
  color: #fff;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
  transition: border-color 0.16s ease, opacity 0.16s ease, transform 0.16s ease;
}

.trade-node:hover,
.trade-node.selected {
  border-color: var(--accent);
  transform: translate(-50%, -50%) scale(1.04);
}

.trade-node.dimmed {
  opacity: 0.35;
}

.node-risk-ring {
  position: absolute;
  inset: 5px;
  border: 1px solid;
  border-radius: 6px;
  opacity: 0.85;
}

.node-name {
  position: relative;
  font-size: 12px;
  font-weight: 500;
}

.node-score {
  position: relative;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.map-legend {
  position: absolute;
  left: 14px;
  bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 10px;
  color: var(--muted);
}

.map-legend i {
  display: inline-block;
  margin-right: 5px;
  vertical-align: middle;
}

.solid-line,
.dashed-line {
  width: 22px;
  height: 0;
  border-top: 2px solid #58a6ff;
}

.dashed-line {
  border-top-style: dashed;
}

.node-dot {
  width: 8px;
  height: 8px;
  border: 1px solid #ef4444;
  border-radius: 999px;
}

.flow-view {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.flow-stage,
.shock-detail,
.evidence-block,
.risk-judgment,
.detail-panel,
.top-corridors,
.flow-summary {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.012);
}

.flow-stage {
  min-height: 330px;
  padding: 14px;
}

.flow-stage-label {
  margin-bottom: 12px;
  font-size: 10px;
  letter-spacing: 0.08em;
  color: var(--muted);
  text-transform: uppercase;
}

.flow-node,
.flow-corridor,
.top-corridor {
  width: 100%;
  text-align: left;
}

.flow-node {
  display: flex;
  min-height: 48px;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 10px;
  color: #fff;
  background: rgba(255, 255, 255, 0.018);
}

.flow-node strong,
.flow-corridor strong,
.top-corridor b {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
}

.flow-summary {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 12px;
}

.flow-corridor {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.018);
}

.flow-corridor p {
  font-size: 12px;
  color: #fff;
}

.flow-corridor span {
  font-size: 10px;
  color: var(--muted);
}

.shock-view {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 12px;
}

.shock-scenarios {
  display: grid;
  gap: 8px;
}

.shock-scenarios button {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  color: #fff;
  background: rgba(255, 255, 255, 0.012);
}

.shock-scenarios button.active {
  border-color: rgba(88, 166, 255, 0.55);
  background: rgba(88, 166, 255, 0.10);
}

.shock-detail {
  padding: 16px;
}

.shock-steps {
  margin-top: 16px;
  display: grid;
  gap: 10px;
}

.shock-step {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

.shock-step span {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border-radius: 6px;
  background: rgba(88, 166, 255, 0.13);
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.shock-step p {
  font-size: 12px;
  line-height: 1.65;
  color: #fff;
}

.evidence-view {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.evidence-block {
  min-height: 150px;
  padding: 16px;
}

.trade-side-panel {
  display: grid;
  gap: 12px;
  align-content: start;
}

.risk-judgment,
.detail-panel,
.top-corridors {
  padding: 16px;
}

.risk-tag {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 3px 7px;
  font-size: 10px;
  color: #fff;
  background: rgba(255, 255, 255, 0.025);
}

.detail-label {
  margin-bottom: 4px;
  font-size: 10px;
  letter-spacing: 0.08em;
  color: var(--muted);
  text-transform: uppercase;
}

.detail-text {
  font-size: 12px;
  line-height: 1.65;
  color: #fff;
}

.top-corridors {
  display: grid;
  gap: 8px;
}

.top-corridor {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.012);
}

.top-corridor.active {
  border-color: rgba(88, 166, 255, 0.50);
  background: rgba(88, 166, 255, 0.09);
}

.top-corridor strong {
  display: block;
  font-size: 12px;
  color: #fff;
}

.top-corridor em {
  display: block;
  margin-top: 3px;
  font-size: 10px;
  font-style: normal;
  color: var(--muted);
}

@media (max-width: 1180px) {
  .trade-atlas-header,
  .shock-view {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .trade-atlas-metrics,
  .flow-view,
  .evidence-view,
  .flow-summary {
    grid-template-columns: 1fr;
  }

  .trade-map-shell {
    min-height: 620px;
  }

  .trade-node {
    width: 74px;
  }
}
</style>
