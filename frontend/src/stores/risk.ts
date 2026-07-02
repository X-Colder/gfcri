import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RiskIndex } from '@/api/types'
import { fetchLatestRisk, fetchRiskHistory } from '@/api/risk'

export const useRiskStore = defineStore('risk', () => {
  const latest = ref<RiskIndex | null>(null)
  const history = ref<RiskIndex[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadLatest() {
    loading.value = true
    error.value = null
    try {
      latest.value = await fetchLatestRisk()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadHistory(limit = 30) {
    try {
      history.value = await fetchRiskHistory(limit)
    } catch (e: any) {
      error.value = e.message
    }
  }

  return { latest, history, loading, error, loadLatest, loadHistory }
})
