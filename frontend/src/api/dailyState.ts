import client from './client'
import type { DailyState } from './types'

export async function fetchLatestState(): Promise<DailyState> {
  const { data } = await client.get('/daily-state/latest')
  return data
}

export async function fetchStateHistory(limit = 30): Promise<DailyState[]> {
  const { data } = await client.get('/daily-state/history', { params: { limit } })
  return data
}
