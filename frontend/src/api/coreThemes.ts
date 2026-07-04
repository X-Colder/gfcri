import client from './client'
import type { CoreThemes } from './types'

export async function fetchCoreThemes(limit = 6, includeCausal = false): Promise<CoreThemes> {
  const { data } = await client.get('/core-themes/latest', {
    params: { limit, include_causal: includeCausal },
  })
  return data
}
