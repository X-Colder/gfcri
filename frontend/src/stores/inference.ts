import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { InferenceResponse } from '@/api/types'
import {
  runPathAnalysis,
  runObservational,
  runInterventional,
  runConfounding,
  fetchInferenceHistory,
} from '@/api/inference'

export const useInferenceStore = defineStore('inference', () => {
  const result = ref<InferenceResponse | null>(null)
  const history = ref<any[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function pathAnalysis(source: string, target: string) {
    loading.value = true
    error.value = null
    try {
      result.value = await runPathAnalysis(source, target)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function observational(source: string, target: string, value: number) {
    loading.value = true
    error.value = null
    try {
      result.value = await runObservational(source, target, value)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function interventional(source: string, target: string, value: number) {
    loading.value = true
    error.value = null
    try {
      result.value = await runInterventional(source, target, value)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function confounding(source: string, target: string) {
    loading.value = true
    error.value = null
    try {
      result.value = await runConfounding(source, target)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadHistory(source?: string, target?: string, limit = 50) {
    try {
      history.value = await fetchInferenceHistory(source, target, limit)
    } catch (e: any) {
      error.value = e.message
    }
  }

  return { result, history, loading, error, pathAnalysis, observational, interventional, confounding, loadHistory }
})
