<template>
  <div class="space-y-6">
    <h2 class="text-xl font-bold">{{ t('graph.title') }}</h2>

    <LoadingSpinner v-if="graphStore.loading" />

    <template v-else-if="graphStore.data">
      <div class="flex gap-2 mb-4">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="px-4 py-1.5 rounded-lg text-sm transition-colors"
          :class="activeTab === tab.key ? 'bg-accent/20 text-accent' : 'text-muted hover:text-white'"
          @click="activeTab = tab.key"
        >{{ tab.label }}</button>
      </div>

      <div v-show="activeTab === 'network'" class="bg-card border border-border rounded-xl p-4" style="height: 600px">
        <svg ref="svgRef" class="w-full h-full"></svg>
      </div>

      <div v-show="activeTab === 'nodes'" class="bg-card border border-border rounded-xl p-4 overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-muted border-b border-border">
              <th class="text-left py-2 px-3">ID</th>
              <th class="text-left py-2 px-3">{{ t('graph.name') }}</th>
              <th class="text-left py-2 px-3">{{ t('graph.type') }}</th>
              <th class="text-left py-2 px-3">{{ t('graph.assetClass') }}</th>
              <th class="text-left py-2 px-3">{{ t('graph.geo') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(node, id) in graphStore.data.nodes" :key="id" class="border-b border-border/50 hover:bg-white/5">
              <td class="py-2 px-3 font-mono text-xs">{{ id }}</td>
              <td class="py-2 px-3">{{ tx(node.display_name) }}</td>
              <td class="py-2 px-3 text-muted">{{ node.node_type }}</td>
              <td class="py-2 px-3">
                <span class="px-2 py-0.5 rounded text-xs" :style="{ color: ASSET_CLASS_COLORS[node.asset_class] || '#8b949e' }">
                  {{ node.asset_class }}
                </span>
              </td>
              <td class="py-2 px-3 text-muted">{{ node.geography }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-show="activeTab === 'edges'" class="bg-card border border-border rounded-xl p-4 overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-muted border-b border-border">
              <th class="text-left py-2 px-3">{{ t('graph.source') }}</th>
              <th class="text-left py-2 px-3">{{ t('graph.target') }}</th>
              <th class="text-left py-2 px-3">{{ t('common.strength') }}</th>
              <th class="text-left py-2 px-3">{{ t('common.confidence') }}</th>
              <th class="text-left py-2 px-3">{{ t('common.lag') }}</th>
              <th class="text-left py-2 px-3">{{ t('common.mechanism') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(edge, id) in graphStore.data.edges" :key="id" class="border-b border-border/50 hover:bg-white/5">
              <td class="py-2 px-3 font-mono text-xs">{{ edge.source_node }}</td>
              <td class="py-2 px-3 font-mono text-xs">{{ edge.target_node }}</td>
              <td class="py-2 px-3 font-mono" :style="{ color: edge.causal_strength > 0 ? '#2ea043' : '#f85149' }">
                {{ edge.causal_strength.toFixed(2) }}
              </td>
              <td class="py-2 px-3 text-muted">{{ edge.strength_confidence.toFixed(2) }}</td>
              <td class="py-2 px-3 text-muted">{{ edge.peak_lag_days }}</td>
              <td class="py-2 px-3 text-muted text-xs">{{ edge.mechanism }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useGraphStore } from '@/stores/graph'
import { ASSET_CLASS_COLORS } from '@/composables/useTheme'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useI18n } from '@/composables/useI18n'

const graphStore = useGraphStore()
const { t, tx } = useI18n()
const svgRef = ref<SVGSVGElement | null>(null)
const activeTab = ref('network')
const tabs = computed(() => [
  { key: 'network', label: t('graph.network') },
  { key: 'nodes', label: t('graph.nodes') },
  { key: 'edges', label: t('graph.edges') },
])

onMounted(() => {
  graphStore.load()
})

watch(() => graphStore.data, async (data) => {
  if (data && activeTab.value === 'network') {
    await nextTick()
    renderGraph()
  }
})

watch(activeTab, async (tab) => {
  if (tab === 'network' && graphStore.data) {
    await nextTick()
    renderGraph()
  }
})

function renderGraph() {
  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()

  const data = graphStore.data
  if (!data || !svgRef.value) return

  const width = svgRef.value.clientWidth
  const height = svgRef.value.clientHeight

  const nodes = Object.entries(data.nodes).map(([id, n]: [string, any]) => ({
    id,
    name: tx(n.display_name),
    assetClass: n.asset_class,
  }))

  const links = Object.values(data.edges).map((e: any) => ({
    source: e.source_node,
    target: e.target_node,
    strength: e.causal_strength,
  }))

  const g = svg.append('g')

  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.3, 3])
    .on('zoom', (event) => g.attr('transform', event.transform))
  svg.call(zoom as any)

  svg.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#8b949e')

  const simulation = d3.forceSimulation(nodes as any)
    .force('link', d3.forceLink(links).id((d: any) => d.id).distance(120))
    .force('charge', d3.forceManyBody().strength(-800))
    .force('center', d3.forceCenter(width / 2, height / 2))

  const link = g.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', (d: any) => d.strength > 0 ? '#2ea04380' : '#f8514980')
    .attr('stroke-width', (d: any) => Math.max(1, Math.abs(d.strength) * 4))
    .attr('marker-end', 'url(#arrowhead)')

  const node = g.append('g')
    .selectAll('circle')
    .data(nodes)
    .join('circle')
    .attr('r', 8)
    .attr('fill', (d: any) => ASSET_CLASS_COLORS[d.assetClass] || '#8b949e')
    .attr('stroke', '#0e1117')
    .attr('stroke-width', 2)
    .call(d3.drag<any, any>()
      .on('start', (event, d: any) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x; d.fy = d.y
      })
      .on('drag', (event, d: any) => { d.fx = event.x; d.fy = event.y })
      .on('end', (event, d: any) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null; d.fy = null
      })
    )

  const label = g.append('g')
    .selectAll('text')
    .data(nodes)
    .join('text')
    .text((d: any) => d.name)
    .attr('font-size', 9)
    .attr('fill', '#e6edf3')
    .attr('dx', 12)
    .attr('dy', 4)

  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)
    node
      .attr('cx', (d: any) => d.x)
      .attr('cy', (d: any) => d.y)
    label
      .attr('x', (d: any) => d.x)
      .attr('y', (d: any) => d.y)
  })
}
</script>
