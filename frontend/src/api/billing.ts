import client from './client'

export async function createCheckout(plan: 'monthly' | 'annual'): Promise<{ checkout_url: string }> {
  const { data } = await client.post('/billing/checkout', { plan })
  return data
}

export async function fetchBillingStatus(): Promise<Record<string, any>> {
  const { data } = await client.get('/billing/status')
  return data
}
