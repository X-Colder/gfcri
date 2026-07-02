import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Report } from '@/api/types'
import { fetchLatestReport } from '@/api/report'

export const useReportStore = defineStore('report', () => {
  const latest = ref<Report | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadLatest() {
    loading.value = true
    error.value = null
    try {
      latest.value = await fetchLatestReport()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { latest, loading, error, loadLatest }
})
