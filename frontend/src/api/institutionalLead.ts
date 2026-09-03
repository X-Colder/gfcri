import client from './client'

export interface InstitutionalLeadPayload {
  company_name: string
  work_email: string
  full_name: string
  role: string
  team_size: string
  use_case: string
  deployment: string
  message: string
  language: 'zh' | 'en'
}

export async function submitInstitutionalLead(payload: InstitutionalLeadPayload) {
  const { data } = await client.post('/billing/institutional-leads', payload)
  return data as { status: string; lead_id: number }
}
