import client from './client'
import type { Report } from './types'

export async function fetchLatestReport(): Promise<Report> {
  const { data } = await client.get('/reports/latest')
  return data
}
