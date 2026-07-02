import client from './client'
import type { AlertItem, SocialContent } from './types'

export async function fetchAlerts(): Promise<{ alerts: AlertItem[] }> {
  const { data } = await client.get('/alerts/latest')
  return data
}

export async function fetchWechatContent(): Promise<SocialContent> {
  const { data } = await client.get('/social/wechat/latest')
  return data
}

export async function fetchZsxqContent(): Promise<SocialContent> {
  const { data } = await client.get('/social/zsxq/latest')
  return data
}

export function getCardImageUrl(): string {
  return '/api/social/card/latest'
}
