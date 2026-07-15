<template>
  <div class="space-y-6">
    <section class="terminal-section p-5">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p class="terminal-kicker">Data Source Governance</p>
          <h1 class="terminal-title">{{ lang === 'zh' ? '数据源管理' : 'Data Sources' }}</h1>
          <p class="terminal-copy mt-2 max-w-4xl">
            {{ lang === 'zh'
              ? '统一展示 GFCRI 当前接入、缓存、观察和计划接入的数据源。新增贸易数据先作为独立分析域运行，暂不进入核心 GFCRI 评分。'
              : 'A unified inventory of sources connected, cached, monitored, or planned by GFCRI. Trade data is currently a standalone analysis domain and does not affect core GFCRI scoring.' }}
          </p>
        </div>
        <button
          class="rounded-lg border border-[var(--border)] px-4 py-2 text-xs font-medium text-white transition hover:border-[var(--accent)] hover:text-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="loading"
          @click="loadOverview"
        >
          {{ loading ? t('common.loading') : (lang === 'zh' ? '刷新' : 'Refresh') }}
        </button>
      </div>

      <div class="mt-5 grid gap-3 md:grid-cols-4">
        <div class="terminal-metric">
          <span>{{ lang === 'zh' ? '数据源总数' : 'Sources' }}</span>
          <strong>{{ overview?.summary?.source_count ?? '-' }}</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ lang === 'zh' ? '核心评分源' : 'Core sources' }}</span>
          <strong>{{ overview?.summary?.core_source_count ?? '-' }}</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ lang === 'zh' ? '独立分析源' : 'Standalone' }}</span>
          <strong>{{ overview?.summary?.standalone_source_count ?? '-' }}</strong>
        </div>
        <div class="terminal-metric">
          <span>{{ lang === 'zh' ? 'A/B 级覆盖' : 'Tier A/B share' }}</span>
          <strong>{{ overview?.summary?.tier_a_b_share ?? '-' }}%</strong>
        </div>
      </div>

      <div class="mt-5 rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
        <p class="text-sm font-medium text-white">{{ lang === 'zh' ? '治理边界' : 'Governance Boundary' }}</p>
        <p class="mt-2 text-xs leading-relaxed text-[var(--muted)]">
          {{ overview?.governance?.principle || '-' }}
        </p>
        <p class="mt-2 text-xs leading-relaxed text-[var(--muted)]">
          {{ overview?.governance?.promotion_gate || '-' }}
        </p>
      </div>
    </section>

    <section class="terminal-section p-5">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="terminal-kicker">{{ lang === 'zh' ? 'Registry' : 'Registry' }}</p>
          <h2 class="mt-1 text-base font-medium text-white">{{ lang === 'zh' ? '接入数据源' : 'Connected Data Sources' }}</h2>
        </div>
        <div class="source-filters">
          <button
            v-for="category in categories"
            :key="category"
            type="button"
            :class="{ active: activeCategory === category }"
            @click="activeCategory = category"
          >
            {{ categoryLabel(category) }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="mt-5 rounded-lg border border-[var(--border)] bg-white/[0.012] p-5 text-sm text-[var(--muted)]">
        {{ t('common.loading') }}
      </div>
      <div v-else-if="error" class="mt-5 rounded-lg border border-red-500/30 bg-red-500/10 p-5 text-sm text-red-100">
        {{ error }}
      </div>
      <div v-else class="mt-5 source-table">
        <article v-for="source in filteredSources" :key="source.source_id" class="source-row">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <span class="status-pill" :class="statusClass(source.status)">{{ source.status }}</span>
              <span class="rounded border border-[var(--border)] px-2 py-0.5 text-[10px] text-[var(--muted)]">{{ categoryLabel(source.category) }}</span>
              <span class="rounded border border-[var(--border)] px-2 py-0.5 text-[10px] text-[var(--muted)]">Tier {{ source.tier }}</span>
              <span class="rounded px-2 py-0.5 text-[10px]" :class="source.affects_core_gfcri ? 'bg-red-500/10 text-red-100' : 'bg-emerald-400/10 text-emerald-100'">
                {{ source.affects_core_gfcri ? (lang === 'zh' ? '进入核心评分' : 'Core scoring') : (lang === 'zh' ? '独立/辅助' : 'Standalone/support') }}
              </span>
            </div>
            <h3 class="mt-2 text-sm font-medium text-white">{{ source.name }}</h3>
            <p class="mt-1 text-xs text-[var(--muted)]">{{ source.provider }} · {{ source.source_type }} · {{ source.update_frequency }}</p>
            <p class="mt-3 text-xs leading-relaxed text-[var(--muted)]">{{ source.limitations }}</p>
          </div>
          <div class="source-row-side">
            <p class="text-[10px] uppercase tracking-wide text-[var(--muted)]">{{ lang === 'zh' ? '使用位置' : 'Used By' }}</p>
            <p class="mt-1 text-xs leading-relaxed text-white">{{ compact(source.used_by) }}</p>
            <p class="mt-3 text-[10px] uppercase tracking-wide text-[var(--muted)]">{{ lang === 'zh' ? '下一步' : 'Next Step' }}</p>
            <p class="mt-1 text-xs leading-relaxed text-white">{{ source.next_step }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.8fr)]">
      <div class="terminal-section p-5">
        <p class="terminal-kicker">{{ lang === 'zh' ? 'Model Source Map' : 'Model Source Map' }}</p>
        <h2 class="mt-1 text-base font-medium text-white">{{ lang === 'zh' ? '模型节点来源分布' : 'Model Node Source Distribution' }}</h2>
        <div class="mt-4 grid gap-3 md:grid-cols-2">
          <article v-for="source in modelNodeSources" :key="source.source_id" class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <h3 class="text-sm font-medium text-white">{{ source.name }}</h3>
                <p class="mt-1 text-xs text-[var(--muted)]">{{ source.node_count }} nodes</p>
              </div>
              <strong class="font-mono text-xl font-medium text-[var(--accent)]">{{ source.node_count }}</strong>
            </div>
            <p class="mt-3 text-xs leading-relaxed text-[var(--muted)]">
              {{ Object.entries(source.tier_counts || {}).map(([tier, count]) => `Tier ${tier}: ${count}`).join(' · ') }}
            </p>
          </article>
        </div>
      </div>

      <aside class="terminal-section p-5">
        <p class="terminal-kicker">{{ lang === 'zh' ? 'Upgrade Queue' : 'Upgrade Queue' }}</p>
        <h2 class="mt-1 text-base font-medium text-white">{{ lang === 'zh' ? '待升级数据源' : 'Source Upgrade Priorities' }}</h2>
        <div class="mt-4 space-y-3">
          <article v-for="item in upgradeCatalog" :key="item.name" class="rounded-lg border border-[var(--border)] bg-white/[0.012] p-3">
            <div class="flex items-start justify-between gap-3">
              <p class="text-sm font-medium text-white">{{ item.name }}</p>
              <span class="rounded bg-[var(--accent)]/10 px-2 py-1 text-[10px] text-[var(--accent)]">{{ item.priority }}</span>
            </div>
            <p class="mt-2 text-xs leading-relaxed text-[var(--muted)]">{{ item.value }}</p>
            <p class="mt-2 text-[11px] text-white">{{ compact(item.sources || []) }}</p>
          </article>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchDataSourceOverview } from '@/api/dataSources'
import type { DataSourceCard, DataSourceOverview } from '@/api/types'
import { useI18n } from '@/composables/useI18n'

const { t, lang } = useI18n()
const overview = ref<DataSourceOverview | null>(null)
const loading = ref(false)
const error = ref('')
const activeCategory = ref('all')

const sources = computed(() => overview.value?.sources || [])
const categories = computed(() => ['all', ...Array.from(new Set(sources.value.map((source) => source.category)))])
const filteredSources = computed(() =>
  activeCategory.value === 'all'
    ? sources.value
    : sources.value.filter((source) => source.category === activeCategory.value)
)
const modelNodeSources = computed(() => (overview.value?.model_node_sources || []).slice(0, 8))
const upgradeCatalog = computed(() => overview.value?.upgrade_catalog || [])

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    overview.value = await fetchDataSourceOverview()
  } catch (err: any) {
    error.value = err?.message || 'load failed'
  } finally {
    loading.value = false
  }
}

function categoryLabel(category: string): string {
  const labels: Record<string, string> = {
    all: lang.value === 'zh' ? '全部' : 'All',
    market_cache: lang.value === 'zh' ? '市场缓存' : 'Market cache',
    model_registry: lang.value === 'zh' ? '模型注册表' : 'Model registry',
    trade: lang.value === 'zh' ? '贸易数据' : 'Trade',
    institutional_radar: lang.value === 'zh' ? '机构雷达' : 'Radar',
  }
  return labels[category] || category
}

function statusClass(status: string): string {
  if (['ok', 'active'].includes(status)) return 'ok'
  if (['degraded', 'error'].includes(status)) return 'warning'
  return 'neutral'
}

function compact(values: DataSourceCard['used_by']): string {
  if (!values?.length) return '-'
  return values.slice(0, 4).join(' / ') + (values.length > 4 ? ` +${values.length - 4}` : '')
}

onMounted(loadOverview)
</script>

<style scoped>
.source-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px;
  background: rgba(255, 255, 255, 0.018);
}

.source-filters button {
  min-height: 30px;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 11px;
  color: var(--muted);
}

.source-filters button.active {
  background: rgba(88, 166, 255, 0.13);
  color: #fff;
}

.source-table {
  display: grid;
  gap: 10px;
}

.source-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.55fr);
  gap: 18px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.012);
}

.source-row-side {
  border-left: 1px solid var(--border);
  padding-left: 16px;
}

.status-pill {
  border-radius: 6px;
  padding: 2px 7px;
  font-size: 10px;
  text-transform: uppercase;
}

.status-pill.ok {
  background: rgba(52, 211, 153, 0.10);
  color: #bbf7d0;
}

.status-pill.warning {
  background: rgba(245, 158, 11, 0.12);
  color: #fde68a;
}

.status-pill.neutral {
  background: rgba(255, 255, 255, 0.06);
  color: var(--muted);
}

@media (max-width: 900px) {
  .source-row {
    grid-template-columns: 1fr;
  }

  .source-row-side {
    border-left: 0;
    border-top: 1px solid var(--border);
    padding-left: 0;
    padding-top: 14px;
  }
}
</style>
