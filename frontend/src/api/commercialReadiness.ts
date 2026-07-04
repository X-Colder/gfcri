import client from './client'
import type { CommercialReadiness } from './types'

export async function fetchCommercialReadiness(): Promise<CommercialReadiness> {
  const { data } = await client.get('/commercial-readiness/latest')
  return data
}
