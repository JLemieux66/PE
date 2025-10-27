import axios from 'axios'
import type { Investment, PEFirm, Stats, CompanyFilters } from '../types/company'

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

export const fetchInvestments = async (filters: CompanyFilters = {}): Promise<Investment[]> => {
  const { data } = await api.get<Investment[]>('/investments', { params: filters })
  return data
}

export const fetchIndustries = async (): Promise<string[]> => {
  const investments = await fetchInvestments({ limit: 1000 })
  const industries = new Set(investments.map(inv => inv.industry_category).filter((ind): ind is string => Boolean(ind)))
  return Array.from(industries).sort()
}
