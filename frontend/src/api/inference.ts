import client from './client'
import type { InferenceResponse } from './types'

export async function runPathAnalysis(source: string, target: string): Promise<InferenceResponse> {
  const { data } = await client.post('/inference/path-analysis', { source, target })
  return data
}

export async function runObservational(source: string, target: string, sourceValue: number): Promise<InferenceResponse> {
  const { data } = await client.post('/inference/observational', { source, target, source_value: sourceValue })
  return data
}

export async function runInterventional(source: string, target: string, interventionValue: number): Promise<InferenceResponse> {
  const { data } = await client.post('/inference/interventional', { source, target, intervention_value: interventionValue })
  return data
}

export async function runConfounding(source: string, target: string): Promise<InferenceResponse> {
  const { data } = await client.post('/inference/confounding', { source, target })
  return data
}

export async function fetchInferenceHistory(source?: string, target?: string, limit = 50) {
  const { data } = await client.get('/inference/history', { params: { source, target, limit } })
  return data
}
