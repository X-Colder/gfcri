import client from './client'
import type { RiskIndex } from './types'

export async function fetchLatestRisk(): Promise<RiskIndex> {
  const { data } = await client.get('/risk-index/latest')
  return data
}

export async function fetchRiskHistory(limit = 30): Promise<RiskIndex[]> {
  const { data } = await client.get('/risk-index/history', { params: { limit } })
  return data
}
