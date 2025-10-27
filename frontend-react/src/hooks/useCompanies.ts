import { useQuery } from '@tanstack/react-query'
import { fetchStats, fetchPEFirms, fetchCompanies, fetchIndustries } from '../api/client'
import type { CompanyFilters } from '../types/company'

export const useStats = () => {
  return useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
  })
}

export const usePEFirms = () => {
  return useQuery({
    queryKey: ['pe-firms'],
    queryFn: fetchPEFirms,
  })
}

export const useCompanies = (filters: CompanyFilters = {}) => {
  return useQuery({
    queryKey: ['companies', filters],
    queryFn: () => fetchCompanies(filters),
  })
}

export const useIndustries = () => {
  return useQuery({
    queryKey: ['industries'],
    queryFn: fetchIndustries,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}
