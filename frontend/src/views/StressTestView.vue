<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold">{{ t('stress.title') }}</h2>
      <button @click="runAll" :disabled="loading" class="px-4 py-2 rounded-lg bg-accent/15 text-accent text-sm font-medium hover:bg-accent/20 transition-colors disabled:opacity-50">
        {{ loading ? t('stress.running') : t('stress.run') }}
      </button>
    </div>

    <LoadingSpinner v-if="loading" />

    <template v-if="results.length">
      <!-- Baseline Crisis Distance -->
      <div v-if="crisisBaseline" class="bg-card border border-border rounded-xl p-5">
        <div class="flex items-center justify-between mb-4">
          <p class="text-sm font-medium">{{ t('stress.baseline') }}</p>
          <div class="text-center">
            <span class="text-3xl font-bold font-mono" :style="{ color: probColor(crisisBaseline.overall_probability) }">{{ crisisBaseline.overall_distance.toFixed(0) }}%</span>
            <span class="text-xs ml-2" :style="{ color: probColor(crisisBaseline.overall_probability) }">{{ probLabel(crisisBaseline.overall_probability) }}</span>
          </div>
        </div>

        <!-- Tier summaries -->
        <div class="grid grid-cols-3 gap-3 mb-4">
          <div class="bg-bg rounded-lg p-3 text-center">
            <p class="text-[10px] text-muted">{{ t('forward.global') }}</p>
            <p class="text-xl font-bold font-mono" :style="{ color: distColor(crisisBaseline.tier1_distance) }">{{ crisisBaseline.tier1_distance.toFixed(0) }}%</p>
            <p class="text-[9px] text-muted">VIX · {{ t('globe.credit') }} · USD</p>
          </div>
          <div class="bg-bg rounded-lg p-3 text-center">
            <p class="text-[10px] text-muted">{{ t('forward.usCore') }}</p>
            <p class="text-xl font-bold font-mono" :style="{ color: distColor(crisisBaseline.tier2_distance) }">{{ crisisBaseline.tier2_distance.toFixed(0) }}%</p>
            <p class="text-[9px] text-muted">S&P · Treasuries · Oil</p>
          </div>
          <div class="bg-bg rounded-lg p-3 text-center">
            <p class="text-[10px] text-muted">{{ t('forward.regional') }}</p>
            <p class="text-xl font-bold font-mono" :style="{ color: distColor(crisisBaseline.tier3_distance) }">{{ crisisBaseline.tier3_distance.toFixed(0) }}%</p>
            <p class="text-[9px] text-muted">KRW · HSI · EUR</p>
          </div>
        </div>

        <!-- Distance bars grouped by tier -->
        <div v-for="tier in [1,2,3]" :key="tier" class="mb-3">
          <p class="text-[10px] text-muted font-medium mb-1.5">{{ tierLabel(tier) }}</p>
          <div class="space-y-1.5">
            <div v-for="d in crisisBaseline.distances.filter((x: any) => x.tier === tier)" :key="d.node_id">
              <div class="flex items-center justify-between text-xs mb-0.5">
                <div class="flex items-center gap-2">
                  <span>{{ tx(d.name) }}</span>
                  <span class="text-[9px] px-1 py-0.5 rounded" :class="d.status === 'crisis' ? 'bg-alert-red/10 text-alert-red' : d.status === 'warning' ? 'bg-alert-yellow/10 text-alert-yellow' : 'bg-alert-green/10 text-alert-green'">
                    {{ d.status === 'crisis' ? t('forward.danger') : d.status === 'warning' ? t('forward.warn') : t('forward.safe') }}
                  </span>
                </div>
                <span class="font-mono text-muted">{{ d.current_value }} <span class="text-[10px]">| {{ t('forward.warn') }} {{ d.warning_value }} | {{ t('common.crisis') }} {{ d.crisis_value }}</span></span>
              </div>
              <div class="relative h-3 bg-bg rounded-full overflow-hidden">
                <div class="absolute inset-0 flex">
                  <div style="width:40%;background:rgba(46,160,67,0.06)"></div>
                  <div style="width:30%;background:rgba(210,153,34,0.06)"></div>
                  <div style="width:30%;background:rgba(248,81,73,0.06)"></div>
                </div>
                <div class="absolute top-0 h-full rounded-full transition-all" :style="{ width: Math.min(d.distance_pct, 100) + '%', backgroundColor: distColor(d.distance_pct) }"></div>
              </div>
              <p class="text-[9px] text-muted mt-0.5">{{ t('forward.worstHist') }}: {{ tx(d.worst_event) }} ({{ d.worst_value }})</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Policy Buffers -->
      <div v-if="crisisBaseline && crisisBaseline.policies.length" class="bg-card border border-border rounded-xl p-5">
        <p class="text-sm font-medium mb-3">{{ t('forward.policy') }}</p>
        <div class="grid grid-cols-3 gap-2">
          <div v-for="p in crisisBaseline.policies" :key="p.name" class="bg-bg rounded-lg p-2.5">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[11px] font-medium">{{ tx(p.name) }}</span>
              <span class="text-[9px] px-1 py-0.5 rounded" :class="p.status === 'buffer' ? 'bg-alert-green/10 text-alert-green' : p.status === 'warning' ? 'bg-alert-red/10 text-alert-red' : 'bg-alert-yellow/10 text-alert-yellow'">
                {{ p.status === 'buffer' ? t('forward.hasBuffer') : p.status === 'warning' ? t('forward.warning') : t('forward.neutral') }}
              </span>
            </div>
            <div class="h-1 bg-border rounded-full overflow-hidden">
              <div class="h-full rounded-full" :style="{ width: p.score + '%', backgroundColor: p.status === 'buffer' ? '#2ea043' : p.status === 'warning' ? '#f85149' : '#d29922' }"></div>
            </div>
            <p class="text-[9px] text-muted mt-1">{{ tx(p.detail) }}</p>
          </div>
        </div>
      </div>

      <!-- Stress Test Scenarios -->
      <p class="text-sm font-medium text-muted">{{ t('stress.scenarioIntro') }}</p>

      <div class="space-y-3">
        <div v-for="r in results" :key="r.scenario_name" class="bg-card border border-border rounded-xl overflow-hidden">
          <div class="p-4 flex items-center justify-between cursor-pointer hover:bg-white/[0.02]" @click="toggle(r)">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 rounded-xl flex items-center justify-center text-base font-bold font-mono" :style="{ backgroundColor: impactColor(r.gfcri_delta) + '15', color: impactColor(r.gfcri_delta) }">
                +{{ r.gfcri_delta.toFixed(0) }}
              </div>
              <div>
                <p class="text-sm font-medium">{{ tx(r.scenario_name) }}</p>
                <p class="text-[11px] text-muted">{{ tx(r.scenario_description) }}</p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div class="text-right">
                <p class="text-sm font-mono">
                  <span class="text-muted">{{ r.baseline_gfcri.toFixed(1) }}</span>
                  <span class="text-muted mx-1">→</span>
                  <span :style="{ color: impactColor(r.gfcri_delta) }">{{ r.stressed_gfcri.toFixed(1) }}</span>
                </p>
                <p class="text-[10px] text-muted">GFCRI</p>
              </div>
              <svg class="w-4 h-4 text-muted transition-transform" :class="expanded === r.scenario_name ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
            </div>
          </div>

          <div v-if="expanded === r.scenario_name" class="border-t border-border">
            <!-- Shocks -->
            <div class="p-4 bg-alert-red/[0.03] border-b border-border">
              <p class="text-xs font-medium text-alert-red mb-2">{{ t('stress.shocks') }}</p>
              <div class="grid grid-cols-2 gap-2">
                <div v-for="s in r.shock_details" :key="s.node" class="bg-bg rounded-lg px-3 py-2">
                  <p class="text-xs font-medium">{{ tx(s.name) }}</p>
                  <p class="text-sm font-mono mt-0.5">
                    <span class="text-muted">{{ s.baseline_price }}</span>
                    <span class="text-alert-red mx-1">→</span>
                    <span class="text-alert-red font-bold">{{ s.stressed_price }}</span>
                    <span class="text-[10px] text-muted ml-1">{{ s.unit }}</span>
                  </p>
                </div>
              </div>
            </div>

            <!-- Flow chart -->
            <div class="p-4 border-b border-border">
              <p class="text-xs font-medium text-muted mb-3">{{ t('stress.flow') }}</p>
              <v-chart :option="buildFlowChart(r)" style="height: 360px" autoresize />
            </div>

            <!-- Propagation steps -->
            <div class="p-4 border-b border-border">
              <p class="text-xs font-medium text-muted mb-3">{{ t('stress.steps') }}</p>
              <div class="space-y-0">
                <div v-for="(step, i) in r.propagation_chain" :key="i">
                  <div v-if="i > 0" class="pl-6 py-0.5"><div class="w-px h-3 bg-border"></div></div>
                  <div class="flex items-start gap-2.5">
                    <div class="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0 mt-0.5" :style="{ backgroundColor: impactColor(Math.abs(step.delta)*3) + '20', color: impactColor(Math.abs(step.delta)*3) }">{{ i+1 }}</div>
                    <div class="flex-1 bg-bg rounded-lg p-2.5">
                      <div class="flex items-center gap-1.5 mb-1">
                        <span class="text-[11px] text-muted">{{ tx(step.caused_by_name) }}</span>
                        <svg class="w-2.5 h-2.5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                        <span class="text-[11px] font-medium">{{ tx(step.name) }}</span>
                        <span class="text-[9px] px-1 py-0.5 rounded ml-auto" :class="step.confidence > 0.5 ? 'bg-alert-green/10 text-alert-green' : 'bg-alert-yellow/10 text-alert-yellow'">{{ (step.confidence*100).toFixed(0) }}%</span>
                      </div>
                      <p class="text-xs font-mono">
                        {{ step.baseline_price }} <span :style="{color: impactColor(Math.abs(step.delta)*3)}">→ {{ step.stressed_price }}</span> {{ step.unit }}
                        <span class="ml-1.5" :style="{color: step.delta>0?'#f85149':'#2ea043'}">{{ step.delta>0?'↑':'↓' }}{{ Math.abs(step.delta).toFixed(1) }}σ</span>
                      </p>
                      <p class="text-[10px] text-muted mt-0.5">{{ tx(step.explanation) }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Vulnerable nodes -->
            <div class="p-4">
              <p class="text-xs font-medium text-muted mb-2">{{ t('stress.vulnerable') }}</p>
              <div class="flex gap-2 overflow-x-auto pb-1">
                <div v-for="v in r.most_vulnerable_nodes.slice(0,6)" :key="v.node" class="shrink-0 bg-bg rounded-lg px-3 py-2 text-center min-w-[80px]">
                  <p class="text-[11px]">{{ tx(v.name) }}</p>
                  <p class="text-lg font-bold font-mono" :style="{color:impactColor(v.impact*3)}">{{ v.impact.toFixed(1) }}</p>
                  <p class="text-[9px] text-muted">{{ t('stress.impactSigma') }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import client from '@/api/client'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useI18n } from '@/composables/useI18n'

use([GraphChart, TooltipComponent, CanvasRenderer])

const results = ref<any[]>([])
const loading = ref(false)
const expanded = ref<string | null>(null)
const { t, tx } = useI18n()

const crisisBaseline = computed(() => results.value.length ? results.value[0].baseline_crisis_distance : null)

onMounted(() => { runAll() })

async function runAll() {
  loading.value = true
  try { results.value = (await client.get('/stress-test/run-all')).data } catch {}
  finally { loading.value = false }
}

function toggle(r: any) { expanded.value = expanded.value === r.scenario_name ? null : r.scenario_name }

function impactColor(d: number): string {
  if (d >= 20) return '#f85149'; if (d >= 10) return '#db6d28'; if (d >= 5) return '#d29922'; return '#2ea043'
}
function probColor(p: string): string {
  return { low: '#2ea043', medium: '#d29922', high: '#db6d28', critical: '#f85149' }[p] || '#8b949e'
}
function probLabel(p: string): string {
  return { low: t('forward.lowRisk'), medium: t('forward.medRisk'), high: t('forward.highRisk'), critical: t('forward.critRisk') }[p] || p
}
function distColor(d: number): string {
  if (d >= 70) return '#f85149'; if (d >= 50) return '#db6d28'; if (d >= 30) return '#d29922'; return '#2ea043'
}
function tierLabel(tier: number): string {
  return { 1: t('forward.tier1'), 2: t('forward.tier2'), 3: t('forward.tier3') }[tier] || ''
}

function buildFlowChart(r: any) {
  const nodeMap = new Map<string, any>()
  const edges: any[] = []

  for (const s of (r.shock_details || []))
    nodeMap.set(s.node, { name: tx(s.name), id: s.node, label: `${tx(s.name)}\n${s.baseline_price}→${s.stressed_price}`, isShock: true })

  for (const step of r.propagation_chain) {
    if (!nodeMap.has(step.caused_by))
      nodeMap.set(step.caused_by, { name: tx(step.caused_by_name), id: step.caused_by, label: tx(step.caused_by_name), isShock: false })
    if (!nodeMap.has(step.node))
      nodeMap.set(step.node, { name: tx(step.name), id: step.node, label: `${tx(step.name)}\n${step.baseline_price}→${step.stressed_price}`, isShock: false })
    edges.push({ source: step.caused_by, target: step.node, delta: step.delta, confidence: step.confidence, explanation: tx(step.explanation) })
  }

  const levels = new Map<string, number>()
  for (const s of (r.shock_details || [])) levels.set(s.node, 0)
  let changed = true
  while (changed) { changed = false; for (const e of edges) { const sl = levels.get(e.source); if (sl !== undefined && (!levels.has(e.target) || levels.get(e.target)! <= sl)) { levels.set(e.target, sl + 1); changed = true } } }

  const levelNodes = new Map<number, string[]>()
  for (const [nid, lvl] of levels) { if (!levelNodes.has(lvl)) levelNodes.set(lvl, []); levelNodes.get(lvl)!.push(nid) }

  const nodes: any[] = []
  for (const [nid, info] of nodeMap) {
    const lvl = levels.get(nid) || 0; const siblings = levelNodes.get(lvl) || [nid]; const idx = siblings.indexOf(nid)
    const x = (idx - (siblings.length-1)/2) * 180; const y = lvl * 110
    const step = r.propagation_chain.find((s: any) => s.node === nid); const impact = step ? Math.abs(step.delta) : (info.isShock ? 3 : 0)
    nodes.push({ name: nid, x, y, symbolSize: 36 + impact * 8, label: { show: true, formatter: info.label, fontSize: 9, color: '#e6edf3', lineHeight: 13 }, itemStyle: { color: info.isShock ? '#f85149' : impactColor(impact*3), borderColor: '#2d333b', borderWidth: 1 } })
  }

  const links = edges.map(e => ({
    source: e.source, target: e.target,
    lineStyle: { color: e.confidence > 0.5 ? '#58a6ff' : '#d29922', width: 1 + Math.abs(e.delta), curveness: 0.1, type: e.confidence > 0.5 ? 'solid' as const : 'dashed' as const },
    label: { show: true, formatter: (e.delta > 0 ? '↑' : '↓') + Math.abs(e.delta).toFixed(1) + 'σ', fontSize: 9, color: e.delta > 0 ? '#f85149' : '#2ea043' },
  }))

  return {
    tooltip: { trigger: 'item' as const, formatter: (p: any) => { if (p.dataType === 'edge') { const e = edges.find(ed => ed.source === p.data.source && ed.target === p.data.target); return e ? `<div style="max-width:240px;font-size:11px">${e.explanation}<br/><span style="color:#888">${t('common.confidence')}: ${(e.confidence*100).toFixed(0)}%</span></div>` : '' } return '' } },
    series: [{ type: 'graph' as const, layout: 'none' as const, data: nodes, links, roam: true, edgeSymbol: ['none', 'arrow'], edgeSymbolSize: [0, 7] }],
  }
}
</script>
