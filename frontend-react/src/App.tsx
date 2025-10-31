import { useState, useEffect } from 'react'
import { Building2, TrendingUp, Users, Briefcase, Grid3X3, List, Download, LogIn, LogOut } from 'lucide-react'
import { useStats, usePEFirms, useCompanies, useIndustries } from './hooks/useCompanies'
import StatCard from './components/StatCard'
import CompanyList from './components/CompanyList'
import CompanyTable from './components/CompanyTable'
import CompanyModal from './components/CompanyModal'
import LoginModal from './components/LoginModal'
import Filters from './components/Filters'
import { exportToCSV } from './utils/csvExport'
import type { CompanyFilters, Investment } from './types/company'

function App() {
  const [filters, setFilters] = useState<CompanyFilters>({})
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('table')
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [isAdmin, setIsAdmin] = useState(false)
  const [adminEmail, setAdminEmail] = useState<string | null>(null)
  const { data: stats, isLoading: statsLoading } = useStats()
  const { data: peFirms } = usePEFirms()
  const { data: industries } = useIndustries()
  const { data: companies, isLoading: companiesLoading } = useCompanies(filters)

  // Convert Company format to Investment format for backwards compatibility
  const investments: Investment[] = companies?.map(company => ({
    company_id: company.id,
    company_name: company.name,
    pe_firm_name: company.pe_firms[0] || '', // Take first PE firm for display
    status: company.status,
    exit_type: company.exit_type,
    investment_year: company.investment_year,
    headquarters: company.headquarters,
    website: company.website,
    linkedin_url: company.linkedin_url,
    crunchbase_url: company.crunchbase_url,
    revenue_range: company.revenue_range,
    employee_count: company.employee_count,
    industry_category: company.industry_category,
  })) || []

  // Check for existing admin session on mount
  useEffect(() => {
    const token = localStorage.getItem('admin_token')
    const email = localStorage.getItem('admin_email')
    if (token && email) {
      setIsAdmin(true)
      setAdminEmail(email)
    }
  }, [])

  const handleFilterChange = (newFilters: CompanyFilters) => {
    setFilters(newFilters)
  }

  const handleExportCSV = () => {
    if (investments && investments.length > 0) {
      exportToCSV(investments, 'pe-portfolio')
    }
  }

  const handleLoginSuccess = (_token: string, email: string) => {
    setIsAdmin(true)
    setAdminEmail(email)
  }

  const handleLogout = () => {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_email')
    setIsAdmin(false)
    setAdminEmail(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Briefcase className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">PE Portfolio Dashboard</h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-500">
                {stats && `${stats.total_companies.toLocaleString()} Companies · ${stats.total_pe_firms} Firms`}
              </div>
              {isAdmin ? (
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-600">{adminEmail}</span>
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 px-3 py-1.5 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                >
                  <LogIn className="w-4 h-4" />
                  Admin Login
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="px-4 sm:px-6 lg:px-8 py-8">
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

        {/* Main Content with Sidebar */}
        <div className="flex gap-6">
          {/* Left Sidebar - Filters */}
          <div className="w-80 flex-shrink-0">
            <Filters
              peFirms={peFirms || []}
              industries={industries || []}
              onFilterChange={handleFilterChange}
            />
          </div>

          {/* Right Content - Companies */}
          <div className="flex-1 min-w-0">
            {/* View Controls */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setViewMode('table')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    viewMode === 'table'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                  }`}
                >
                  <List className="w-4 h-4 inline mr-2" />
                  Table
                </button>
                <button
                  onClick={() => setViewMode('cards')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    viewMode === 'cards'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                  }`}
                >
                  <Grid3X3 className="w-4 h-4 inline mr-2" />
                  Cards
                </button>
              </div>
              <button
                onClick={handleExportCSV}
                disabled={!investments || investments.length === 0}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="w-4 h-4 inline mr-2" />
                Export CSV ({investments?.length || 0} companies)
              </button>
            </div>

            {/* Company Display */}
            {viewMode === 'cards' ? (
              <CompanyList
                investments={investments || []}
                isLoading={companiesLoading}
                onCompanyClick={setSelectedCompanyId}
              />
            ) : (
              <CompanyTable
                investments={investments || []}
                loading={companiesLoading}
                onCompanyClick={setSelectedCompanyId}
              />
            )}
          </div>
        </div>
      </div>

      {/* Company Detail Modal */}
      {selectedCompanyId && (
        <CompanyModal
          companyId={selectedCompanyId}
          onClose={() => setSelectedCompanyId(null)}
        />
      )}

      {/* Login Modal */}
      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onLoginSuccess={handleLoginSuccess}
        />
      )}
    </div>
  )
}

export default App
