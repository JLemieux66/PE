export interface Investment {
  company_id: number
  company_name: string
  pe_firm_name: string
  status: string
  raw_status?: string
  exit_type?: string
  exit_info?: string
  investment_year?: string
  sector?: string
  revenue_range?: string
  predicted_revenue?: number
  employee_count?: string
  swarm_headcount?: number  // Actual employee headcount from Swarm API
  industry_category?: string
  headquarters?: string
  website?: string
  linkedin_url?: string
}

export interface Company {
  id: number
  name: string
  pe_firms: string[]
  status: string
  exit_type?: string
  investment_year?: string
  headquarters?: string
  website?: string
  linkedin_url?: string
  description?: string
  revenue_range?: string
  predicted_revenue?: number
  employee_count?: string
  swarm_headcount?: number  // Actual employee headcount from Swarm API
  industry_category?: string
  total_funding_usd?: number
  is_public?: boolean
  stock_exchange?: string
}

export interface PEFirm {
  id: number
  name: string
  total_investments: number
  active_count: number
  exit_count: number
}

export interface Stats {
  total_companies: number
  total_investments: number
  total_pe_firms: number
  active_investments: number
  exited_investments: number
  co_investments: number
  enrichment_rate: number
}

export interface CompanyFilters {
  pe_firm?: string
  status?: string
  exit_type?: string
  industry?: string
  search?: string
  limit?: number
  offset?: number
}
