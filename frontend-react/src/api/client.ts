import axios from 'axios'
import type { Company, PEFirm, Stats, CompanyFilters } from '../types/company'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const fetchStats = async (): Promise<Stats> => {
  const { data } = await api.get<Stats>('/stats')
  return data
}

export const fetchPEFirms = async (): Promise<PEFirm[]> => {
  const { data } = await api.get<PEFirm[]>('/pe-firms')
  return data
}

export const fetchCompanies = async (filters: CompanyFilters = {}): Promise<Company[]> => {
  const { data } = await api.get<Company[]>('/companies', { params: filters })
  return data
}

export const fetchCompanyById = async (id: string): Promise<Company> => {
  const { data } = await api.get<Company>(`/companies/${id}`)
  return data
}

export const fetchIndustries = async (): Promise<string[]> => {
  const companies = await fetchCompanies({ limit: 10000 })
  const industries = new Set(companies.map(company => company.industry_category).filter((ind): ind is string => Boolean(ind)))
  return Array.from(industries).sort()
}
