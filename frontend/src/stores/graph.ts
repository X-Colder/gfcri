import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { GraphData } from '@/api/types'
import { fetchGraph } from '@/api/graph'

export const useGraphStore = defineStore('graph', () => {
  const data = ref<GraphData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load() {
    loading.value = true
    error.value = null
    try {
      data.value = await fetchGraph()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, load }
})
