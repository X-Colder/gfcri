import client from './client'
import type { GraphData } from './types'

export async function fetchGraph(): Promise<GraphData> {
  const { data } = await client.get('/graph')
  return data
}

export async function fetchNodes(): Promise<Record<string, any>> {
  const { data } = await client.get('/graph/nodes')
  return data
}

export async function fetchEdges(): Promise<Record<string, any>> {
  const { data } = await client.get('/graph/edges')
  return data
}
