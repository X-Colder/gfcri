<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold">{{ t('industry.title') }}</h2>
      <button @click="loadScores" :disabled="loading" class="px-4 py-2 rounded-lg bg-accent/15 text-accent text-sm font-medium hover:bg-accent/20 transition-colors disabled:opacity-50">
        {{ loading ? t('common.loading') : t('common.refresh') }}
      </button>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-card border border-border rounded-xl p-1">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="flex-1 py-2 rounded-lg text-sm font-medium transition-all text-center"
        :class="activeTab === tab.key ? 'bg-accent/15 text-accent' : 'text-muted hover:text-white'"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <LoadingSpinner v-if="loading" />

    <!-- Layer 1: Industry Scores -->
    <div v-show="activeTab === 'scores' && !loading">
      <!-- Category Filter -->
      <div class="flex gap-2 flex-wrap mb-4">
        <button
          v-for="cat in [ALL_CATEGORY, ...categories]"
          :key="cat"
          class="px-3 py-1 rounded-lg text-xs transition-colors"
          :class="selectedCategory === cat ? 'bg-accent/20 text-accent' : 'bg-card border border-border text-muted hover:text-white'"
          @click="selectedCategory = cat"
        >{{ cat === ALL_CATEGORY ? t('industry.all') : tx(cat) }}</button>
      </div>

      <div v-if="filteredScores.length" class="space-y-2">
        <div
          v-for="s in filteredScores"
          :key="s.code"
          class="bg-card border border-border rounded-xl p-4 hover:border-accent/30 cursor-pointer transition-all"
          @click="selectedIndustry = s"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold" :style="{ backgroundColor: scoreColor(s.score) + '1a', color: scoreColor(s.score) }">
                {{ s.score.toFixed(0) }}
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium">{{ tx(pickLang(s, 'name_zh', 'name_en')) }}</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-border/50 text-muted">{{ tx(s.category) }}</span>
                </div>
                <div class="flex items-center gap-3 mt-0.5">
                  <span class="text-xs" :class="s.change_1m > 0 ? 'text-alert-green' : s.change_1m < 0 ? 'text-alert-red' : 'text-muted'">
                    {{ t('industry.month') }} {{ s.change_1m > 0 ? '+' : '' }}{{ s.change_1m.toFixed(1) }}%
                  </span>
                  <span class="text-xs" :class="s.change_3m > 0 ? 'text-alert-green' : s.change_3m < 0 ? 'text-alert-red' : 'text-muted'">
                    {{ t('industry.quarter') }} {{ s.change_3m > 0 ? '+' : '' }}{{ s.change_3m.toFixed(1) }}%
                  </span>
                  <span class="text-xs text-muted">{{ t('industry.volatility') }} {{ s.volatility.toFixed(0) }}%</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs px-2 py-0.5 rounded-full" :class="s.trend === 'up' ? 'bg-alert-green/10 text-alert-green' : s.trend === 'down' ? 'bg-alert-red/10 text-alert-red' : 'bg-border text-muted'">
                {{ s.trend === 'up' ? t('industry.up') : s.trend === 'down' ? t('industry.down') : t('industry.flat') }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-muted text-center py-12">{{ t('industry.refreshHint') }}</div>
    </div>

    <!-- Layer 2: Supply Chain -->
    <div v-show="activeTab === 'chain' && !loading">
      <div class="bg-card border border-border rounded-xl p-5">
        <h3 class="text-sm font-medium mb-4">{{ t('industry.chainTitle') }}</h3>
        <div v-if="supplyChain" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-muted mb-2">{{ t('industry.nodes') }} ({{ supplyChain.nodes.length }})</p>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="node in supplyChain.nodes"
                  :key="node.code"
                  class="px-2 py-1 rounded text-[10px] cursor-pointer hover:ring-1 ring-accent transition-all"
                  :style="{ backgroundColor: catColor(node.category) + '15', color: catColor(node.category) }"
                  @click="showChainDetail(node.code)"
                >{{ tx(pickLang(node, 'name_zh', 'name_en')) }}</span>
              </div>
            </div>
            <div>
              <p class="text-xs text-muted mb-2">{{ t('industry.edges') }} ({{ supplyChain.edges.length }})</p>
              <div class="max-h-[300px] overflow-y-auto space-y-1">
                <div v-for="(edge, i) in supplyChain.edges.slice(0, 30)" :key="i" class="flex items-center gap-1 text-[10px]">
                  <span class="text-muted">{{ tx(edge.source_name) }}</span>
                  <span class="text-accent">→</span>
                  <span>{{ tx(edge.target_name) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-muted text-center py-8">
          <button @click="loadSupplyChain" class="text-accent hover:underline text-sm">{{ t('industry.loadChain') }}</button>
        </div>
      </div>

      <!-- Chain Detail -->
      <div v-if="chainDetail" class="bg-card border border-border rounded-xl p-5 mt-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-medium">{{ tx(pickLang(chainDetail, 'name_zh', 'name_en')) }} - {{ t('industry.analysis') }}</h3>
          <button @click="chainDetail = null" class="text-muted hover:text-white text-sm">✕</button>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-xs text-muted mb-2">{{ t('industry.upstream') }}</p>
            <div v-if="chainDetail.upstream?.length" class="space-y-1">
              <div v-for="u in chainDetail.upstream" :key="u.code" class="flex items-center gap-2 bg-bg rounded px-3 py-1.5">
                <span class="text-xs">{{ tx(pickLang(u, 'name_zh', 'name_en')) }}</span>
                <span class="text-[10px] text-muted">{{ tx(u.category) }}</span>
              </div>
            </div>
            <p v-else class="text-xs text-muted">{{ t('industry.source') }}</p>
          </div>
          <div>
            <p class="text-xs text-muted mb-2">{{ t('industry.downstream') }}</p>
            <div v-if="chainDetail.downstream?.length" class="space-y-1">
              <div v-for="d in chainDetail.downstream" :key="d.code" class="flex items-center gap-2 bg-bg rounded px-3 py-1.5">
                <span class="text-xs">{{ tx(pickLang(d, 'name_zh', 'name_en')) }}</span>
                <span class="text-[10px] text-muted">{{ tx(d.category) }}</span>
              </div>
            </div>
            <p v-else class="text-xs text-muted">{{ t('industry.terminal') }}</p>
          </div>
        </div>
        <div v-if="chainDetail.impact_paths?.length" class="mt-4">
          <p class="text-xs text-muted mb-2">{{ t('industry.impactPath') }}</p>
          <div class="space-y-1">
            <div v-for="(p, i) in chainDetail.impact_paths.slice(0, 8)" :key="i" class="flex items-center gap-1 flex-wrap">
              <template v-for="(node, j) in p.path" :key="j">
                <span class="px-1.5 py-0.5 bg-accent/10 text-accent text-[10px] rounded">{{ tx(node) }}</span>
                <span v-if="j < p.path.length - 1" class="text-muted text-[10px]">→</span>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Industry Detail Drawer -->
    <div v-if="selectedIndustry" class="bg-card border border-border rounded-xl p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-medium">{{ tx(pickLang(selectedIndustry, 'name_zh', 'name_en')) }}</h3>
        <button @click="selectedIndustry = null" class="text-muted hover:text-white">✕</button>
      </div>
      <div class="grid grid-cols-4 gap-3 mb-4">
        <MetricCard :label="t('industry.score')" :value="selectedIndustry.score.toFixed(0)" :color="scoreColor(selectedIndustry.score)" />
        <MetricCard :label="t('industry.monthlyChange')" :value="selectedIndustry.change_1m.toFixed(1) + '%'" :color="selectedIndustry.change_1m > 0 ? '#2ea043' : '#f85149'" />
        <MetricCard :label="t('industry.quarterlyChange')" :value="selectedIndustry.change_3m.toFixed(1) + '%'" :color="selectedIndustry.change_3m > 0 ? '#2ea043' : '#f85149'" />
        <MetricCard :label="t('industry.volatility')" :value="selectedIndustry.volatility.toFixed(0) + '%'" />
      </div>
      <div class="mb-3">
        <p class="text-xs text-muted mb-1">{{ t('industry.keyEconomies') }}</p>
        <div class="flex gap-1.5">
          <span v-for="e in selectedIndustry.key_economies" :key="e" class="px-2 py-0.5 bg-border/50 rounded text-xs">{{ e }}</span>
        </div>
      </div>
      <div>
        <p class="text-xs text-muted mb-2">{{ t('industry.trackedAssets') }}</p>
        <table class="w-full text-xs">
          <thead><tr class="text-muted border-b border-border"><th class="text-left py-1.5">{{ t('industry.asset') }}</th><th class="text-right py-1.5">{{ t('industry.price') }}</th><th class="text-right py-1.5">{{ t('industry.monthlyChange') }}</th><th class="text-right py-1.5">{{ t('industry.momentum') }}</th></tr></thead>
          <tbody>
            <tr v-for="t in selectedIndustry.ticker_details" :key="t.ticker" class="border-b border-border/30">
              <td class="py-1.5"><span class="font-mono text-muted">{{ t.ticker }}</span> {{ tx(t.name) }}</td>
              <td class="text-right font-mono">{{ t.price }}</td>
              <td class="text-right font-mono" :class="t.change_1m > 0 ? 'text-alert-green' : 'text-alert-red'">{{ t.change_1m > 0 ? '+' : '' }}{{ t.change_1m }}%</td>
              <td class="text-right font-mono" :style="{ color: scoreColor(t.momentum) }">{{ t.momentum }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import client from '@/api/client'
import MetricCard from '@/components/common/MetricCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useI18n } from '@/composables/useI18n'

const activeTab = ref('scores')
const { t, tx, pickLang } = useI18n()
const ALL_CATEGORY = '全部'
const tabs = computed(() => [
  { key: 'scores', label: t('industry.scores') },
  { key: 'chain', label: t('industry.chain') },
])

const scores = ref<any[]>([])
const loading = ref(false)
const selectedIndustry = ref<any>(null)
const selectedCategory = ref(ALL_CATEGORY)
const categories = ref<string[]>([])
const supplyChain = ref<any>(null)
const chainDetail = ref<any>(null)

const filteredScores = computed(() => {
  if (selectedCategory.value === ALL_CATEGORY) return scores.value
  return scores.value.filter(s => s.category === selectedCategory.value)
})

onMounted(async () => {
  try {
    const { data } = await client.get('/industry/categories')
    categories.value = data
  } catch {}
  loadScores()
  loadSupplyChain()
})

async function loadScores() {
  loading.value = true
  try {
    const { data } = await client.get('/industry/scores')
    scores.value = data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function loadSupplyChain() {
  try {
    const { data } = await client.get('/industry/supply-chain/graph')
    supplyChain.value = data
  } catch (e) { console.error(e) }
}

async function showChainDetail(code: string) {
  try {
    const { data } = await client.get(`/industry/supply-chain/${code}`)
    chainDetail.value = data
  } catch (e) { console.error(e) }
}

function scoreColor(s: number): string {
  if (s >= 70) return '#2ea043'
  if (s >= 50) return '#d29922'
  if (s >= 35) return '#db6d28'
  return '#f85149'
}

function catColor(category: string): string {
  const map: Record<string, string> = {
    '信息技术': '#58a6ff', '能源': '#f0883e', '原材料': '#d29922',
    '工业': '#8b949e', '金融': '#2ea043', '消费': '#bc8cff',
    '医疗健康': '#f85149', '农业': '#5de4c7', '通信': '#db6d28',
  }
  return map[category] || '#8b949e'
}
</script>
