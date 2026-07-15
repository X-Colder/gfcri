import client from './client'
import type { TradeRiskAtlas } from './types'

export async function fetchTradeRiskAtlas(refreshSources = false): Promise<TradeRiskAtlas> {
  const { data } = await client.get('/trade-risk/atlas', {
    params: { refresh_sources: refreshSources },
  })
  return data
}

export async function refreshTradeRiskSources(): Promise<Record<string, any>> {
  const { data } = await client.post('/trade-risk/refresh')
  return data
}
