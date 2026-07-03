import client from './client'
import type { ModelFoundation } from './types'

export async function fetchModelFoundation(): Promise<ModelFoundation> {
  const { data } = await client.get('/model-foundation/latest')
  return data
}
