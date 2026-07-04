import client from './client'
import type { InstitutionalRadar } from './types'

export async function fetchInstitutionalRadar(limit = 30, refresh = false): Promise<InstitutionalRadar> {
  const { data } = await client.get('/institutional-radar/latest', {
    params: { limit, refresh },
  })
  return data
}
