<template>
  <div class="space-y-6">
    <h2 class="text-xl font-bold">{{ t('inference.title') }}</h2>

    <div class="grid grid-cols-12 gap-6">
      <!-- Sidebar Form -->
      <div class="col-span-4 bg-card border border-border rounded-xl p-5 space-y-4">
        <div>
          <label class="text-xs text-muted block mb-1">{{ t('inference.source') }}</label>
          <select v-model="source" class="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm">
            <option v-for="id in nodeIds" :key="id" :value="id">{{ id }}</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-muted block mb-1">{{ t('inference.target') }}</label>
          <select v-model="target" class="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm">
            <option v-for="id in nodeIds" :key="id" :value="id">{{ id }}</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-muted block mb-1">{{ t('inference.type') }}</label>
          <div class="space-y-2">
            <label v-for="t in inferenceTypes" :key="t.key" class="flex items-center gap-2 cursor-pointer">
              <input type="radio" :value="t.key" v-model="inferType" class="accent-[#58a6ff]" />
              <span class="text-sm">{{ t.label }}</span>
            </label>
          </div>
        </div>
        <div v-if="inferType === 'observational'">
          <label class="text-xs text-muted block mb-1">{{ t('inference.observed') }}</label>
          <input v-model.number="sourceValue" type="number" step="0.01" class="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm" />
        </div>
        <div v-if="inferType === 'interventional'">
          <label class="text-xs text-muted block mb-1">{{ t('inference.intervention') }}</label>
          <input v-model.number="interventionValue" type="number" step="0.01" class="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm" />
        </div>
        <button
          @click="runInference"
          :disabled="inferenceStore.loading || !source || !target"
          class="w-full bg-accent hover:bg-accent/80 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium transition-colors"
        >
          {{ inferenceStore.loading ? t('inference.running') : t('inference.run') }}
        </button>
      </div>

      <!-- Results -->
      <div class="col-span-8 space-y-4">
        <LoadingSpinner v-if="inferenceStore.loading" />

        <div v-else-if="inferenceStore.result" class="bg-card border border-border rounded-xl p-5 space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-medium">{{ inferenceStore.result.inference_type }} {{ t('inference.result') }}</h3>
            <span class="text-xs text-muted">{{ t('inference.elapsed') }} {{ inferenceStore.result.computation_time_ms }}ms</span>
          </div>

          <div v-if="inferenceStore.result.result.natural_language_summary" class="text-sm text-muted">
            {{ inferenceStore.result.result.natural_language_summary }}
          </div>

          <div class="grid grid-cols-3 gap-3">
            <MetricCard
              v-if="inferenceStore.result.result.point_estimate !== undefined"
              :label="t('inference.point')"
              :value="Number(inferenceStore.result.result.point_estimate).toFixed(4)"
            />
            <MetricCard
              v-if="inferenceStore.result.result.confidence !== undefined"
              :label="t('common.confidence')"
              :value="Number(inferenceStore.result.result.confidence).toFixed(3)"
            />
            <MetricCard
              v-if="inferenceStore.result.result.total_paths !== undefined"
              :label="t('inference.paths')"
              :value="inferenceStore.result.result.total_paths"
            />
            <MetricCard
              v-if="inferenceStore.result.result.r_squared !== undefined"
              label="R²"
              :value="Number(inferenceStore.result.result.r_squared).toFixed(3)"
            />
          </div>

          <!-- Path details for path_analysis -->
          <div v-if="inferenceStore.result.inference_type === 'path_analysis' && inferenceStore.result.result.paths" class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-muted border-b border-border">
                  <th class="text-left py-2 px-3">{{ t('common.path') }}</th>
                  <th class="text-left py-2 px-3">{{ t('common.strength') }}</th>
                  <th class="text-left py-2 px-3">{{ t('common.lag') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(path, i) in inferenceStore.result.result.paths" :key="i" class="border-b border-border/50">
                  <td class="py-2 px-3 font-mono text-xs">{{ path.path_str || path.path.join(' → ') }}</td>
                  <td class="py-2 px-3 font-mono" :style="{ color: path.strength > 0 ? '#2ea043' : '#f85149' }">{{ path.strength.toFixed(3) }}</td>
                  <td class="py-2 px-3 text-muted">{{ path.total_lag_days }}d</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-else class="text-muted text-center py-12">{{ t('inference.empty') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useInferenceStore } from '@/stores/inference'
import { useGraphStore } from '@/stores/graph'
import MetricCard from '@/components/common/MetricCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useI18n } from '@/composables/useI18n'

const graphStore = useGraphStore()
const inferenceStore = useInferenceStore()
const { t } = useI18n()

const source = ref('dxy')
const target = ref('krw_usd')
const inferType = ref('path_analysis')
const sourceValue = ref(0)
const interventionValue = ref(0)

const inferenceTypes = computed(() => [
  'path_analysis',
  'observational',
  'interventional',
  'confounding',
].map(key => ({ key, label: t(`inference.type.${key}`) })))

const nodeIds = ref<string[]>([])

onMounted(async () => {
  if (!graphStore.data) await graphStore.load()
  if (graphStore.data) {
    nodeIds.value = Object.keys(graphStore.data.nodes)
  }
})

function runInference() {
  switch (inferType.value) {
    case 'path_analysis':
      inferenceStore.pathAnalysis(source.value, target.value)
      break
    case 'observational':
      inferenceStore.observational(source.value, target.value, sourceValue.value)
      break
    case 'interventional':
      inferenceStore.interventional(source.value, target.value, interventionValue.value)
      break
    case 'confounding':
      inferenceStore.confounding(source.value, target.value)
      break
  }
}
</script>
