import { useState } from 'react'
import { Building2, TrendingUp, Users, Briefcase } from 'lucide-react'
import { useStats, usePEFirms, useInvestments } from './hooks/useCompanies'
import StatCard from './components/StatCard'
import CompanyList from './components/CompanyList'
import Filters from './components/Filters'
import type { CompanyFilters } from './types/company'

function App() {
  const [filters, setFilters] = useState<CompanyFilters>({})
  const { data: stats, isLoading: statsLoading } = useStats()
  const { data: peFirms } = usePEFirms()
  const { data: investments, isLoading: investmentsLoading } = useInvestments(filters)

  const handleFilterChange = (newFilters: CompanyFilters) => {
    setFilters(newFilters)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Briefcase className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">PE Portfolio Dashboard</h1>
            </div>
            <div className="text-sm text-gray-500">
              {stats && `${stats.total_companies.toLocaleString()} Companies · ${stats.total_pe_firms} Firms`}
            </div>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {statsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-8 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        ) : stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total Companies"
              value={stats.total_companies.toLocaleString()}
              icon={<Building2 className="w-6 h-6" />}
              color="blue"
            />
            <StatCard
              title="Active Investments"
              value={stats.active_investments.toLocaleString()}
              icon={<TrendingUp className="w-6 h-6" />}
              color="green"
              subtitle={`${((stats.active_investments / stats.total_investments) * 100).toFixed(1)}%`}
            />
            <StatCard
              title="Exited"
              value={stats.exited_investments.toLocaleString()}
              icon={<Users className="w-6 h-6" />}
              color="gray"
              subtitle={`${((stats.exited_investments / stats.total_investments) * 100).toFixed(1)}%`}
            />
            <StatCard
              title="Co-Investments"
              value={stats.co_investments.toLocaleString()}
              icon={<Briefcase className="w-6 h-6" />}
              color="purple"
              subtitle={`${stats.enrichment_rate.toFixed(1)}% enriched`}
            />
          </div>
        )}

        {/* Filters */}
        <Filters
          peFirms={peFirms || []}
          onFilterChange={handleFilterChange}
        />

        {/* Company List */}
        <CompanyList
          investments={investments || []}
          isLoading={investmentsLoading}
        />
      </div>
    </div>
  )
}

export default App
