import client from './client'
import type { DataSourceOverview } from './types'

export async function fetchDataSourceOverview(): Promise<DataSourceOverview> {
  const { data } = await client.get('/data-sources/overview')
  return data
}
