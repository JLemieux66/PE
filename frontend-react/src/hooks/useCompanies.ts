import { useQuery } from '@tanstack/react-query'
import { fetchStats, fetchPEFirms, fetchInvestments, fetchIndustries } from '../api/client'
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

export const useInvestments = (filters: CompanyFilters = {}) => {
  return useQuery({
    queryKey: ['investments', filters],
    queryFn: () => fetchInvestments(filters),
  })
}

export const useIndustries = () => {
  return useQuery({
    queryKey: ['industries'],
    queryFn: fetchIndustries,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}
