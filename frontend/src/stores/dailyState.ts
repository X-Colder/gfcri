import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DailyState } from '@/api/types'
import { fetchLatestState, fetchStateHistory } from '@/api/dailyState'

export const useDailyStateStore = defineStore('dailyState', () => {
  const latest = ref<DailyState | null>(null)
  const history = ref<DailyState[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadLatest() {
    loading.value = true
    error.value = null
    try {
      latest.value = await fetchLatestState()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadHistory(limit = 30) {
    try {
      history.value = await fetchStateHistory(limit)
    } catch (e: any) {
      error.value = e.message
    }
  }

  return { latest, history, loading, error, loadLatest, loadHistory }
})
