import { useState } from 'react'
import { ArrowUpDown, ExternalLink, Building2, MapPin, Users, DollarSign, ChevronLeft, ChevronRight } from 'lucide-react'
import type { Investment } from '../types/company'

interface CompanyTableProps {
  investments: Investment[]
  loading?: boolean
  onCompanyClick?: (companyId: number) => void
}

type SortField = 'company_name' | 'pe_firm_name' | 'status' | 'industry_category' | 'headquarters' | 'employee_count' | 'revenue_range'
type SortDirection = 'asc' | 'desc'

const ITEMS_PER_PAGE = 100

// Helper function to extract domain from URL
const extractDomain = (url: string | null | undefined): string | null => {
  if (!url) return null
  try {
    const domain = url.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0]
    return domain
  } catch {
    return null
  }
}

// Helper function to get company initials
const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

// Company logo component
const CompanyLogo = ({ website, name }: { website: string | null | undefined; name: string }) => {
  const [logoError, setLogoError] = useState(false)
  const domain = extractDomain(website)
  const logoUrl = domain ? `https://logo.clearbit.com/${domain}` : null

  if (logoUrl && !logoError) {
    return (
      <img
        src={logoUrl}
        alt={`${name} logo`}
        onError={() => setLogoError(true)}
        className="w-6 h-6 object-contain rounded flex-shrink-0"
      />
    )
  }

  // Fallback to initials
  return (
    <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-indigo-600 rounded flex items-center justify-center text-white font-bold text-xs flex-shrink-0">
      {getInitials(name)}
    </div>
  )
}

export default function CompanyTable({ investments, loading, onCompanyClick }: CompanyTableProps) {
  const [sortField, setSortField] = useState<SortField>('company_name')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [currentPage, setCurrentPage] = useState(1)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
    setCurrentPage(1) // Reset to first page when sorting
  }

  const sortedInvestments = [...investments].sort((a, b) => {
    // Handle numeric sorting for employee count
    if (sortField === 'employee_count') {
      const aNum = parseInt(a.employee_count || '0')
      const bNum = parseInt(b.employee_count || '0')
      return sortDirection === 'asc' ? aNum - bNum : bNum - aNum
    }
    
    // String comparison
    const aValue = a[sortField] || ''
    const bValue = b[sortField] || ''
    const comparison = String(aValue).localeCompare(String(bValue))
    return sortDirection === 'asc' ? comparison : -comparison
  })

  // Pagination
  const totalPages = Math.ceil(sortedInvestments.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const endIndex = startIndex + ITEMS_PER_PAGE
  const paginatedInvestments = sortedInvestments.slice(startIndex, endIndex)

  const handlePrevPage = () => {
    setCurrentPage(prev => Math.max(1, prev - 1))
  }

  const handleNextPage = () => {
    setCurrentPage(prev => Math.min(totalPages, prev + 1))
  }

  const goToPage = (page: number) => {
    setCurrentPage(page)
  }

  const SortButton = ({ field, label }: { field: SortField; label: string }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center space-x-1 hover:text-blue-600 transition-colors"
    >
      <span>{label}</span>
      <ArrowUpDown className={`w-4 h-4 ${sortField === field ? 'text-blue-600' : 'text-gray-400'}`} />
    </button>
  )

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="animate-pulse p-6">
          <div className="h-10 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (investments.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500">No companies found</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
                <SortButton field="company_name" label="Company" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                <SortButton field="pe_firm_name" label="PE Firm" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                <SortButton field="status" label="Status" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                <SortButton field="industry_category" label="Industry" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                <SortButton field="headquarters" label="HQ" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                <SortButton field="employee_count" label="Employees" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">
                <SortButton field="revenue_range" label="Revenue" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-16">
                Links
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedInvestments.map((investment, index) => (
              <tr 
                key={`${investment.company_name}-${index}`} 
                className="hover:bg-gray-50 transition-colors cursor-pointer"
                onClick={() => onCompanyClick?.(investment.company_id)}
              >
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    <CompanyLogo website={investment.website} name={investment.company_name} />
                    <span className="font-medium text-gray-900 text-sm break-words">{investment.company_name}</span>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <span className="text-sm text-gray-700 break-words">{investment.pe_firm_name}</span>
                </td>
                <td className="px-3 py-3">
                  <div>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      investment.status === 'Active' 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {investment.status}
                    </span>
                    {investment.exit_type && (
                      <div className="text-xs text-gray-500 mt-1">
                        {investment.exit_type}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-3 py-3">
                  <span className="text-sm text-gray-700 break-words">{investment.industry_category || 'N/A'}</span>
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-start text-sm text-gray-700">
                    <MapPin className="w-3 h-3 text-gray-400 mr-1 mt-0.5 flex-shrink-0" />
                    <span className="break-words">{investment.headquarters || 'N/A'}</span>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center text-sm text-gray-700">
                    <Users className="w-3 h-3 text-gray-400 mr-1 flex-shrink-0" />
                    <span className="whitespace-nowrap">{investment.employee_count || 'N/A'}</span>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-start text-sm text-gray-700">
                    <DollarSign className="w-3 h-3 text-gray-400 mr-1 mt-0.5 flex-shrink-0" />
                    <span className="break-words">{investment.revenue_range || 'N/A'}</span>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <div className="flex space-x-2">
                    {investment.website && (
                      <a
                        href={investment.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                        title="Website"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                    {investment.linkedin_url && (
                      <a
                        href={investment.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                        title="LinkedIn"
                      >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                        </svg>
                      </a>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <p className="text-sm text-gray-600">
            Showing {startIndex + 1} to {Math.min(endIndex, sortedInvestments.length)} of {sortedInvestments.length} companies
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handlePrevPage}
            disabled={currentPage === 1}
            className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          
          <div className="flex items-center space-x-1">
            {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => {
              // Show first 3, last 3, and pages around current
              const pageNum = i + 1
              const showPage = 
                pageNum <= 3 || 
                pageNum > totalPages - 3 || 
                (pageNum >= currentPage - 1 && pageNum <= currentPage + 1)
              
              if (!showPage && pageNum === 4 && currentPage > 5) {
                return <span key={i} className="px-2 text-gray-500">...</span>
              }
              if (!showPage && pageNum === totalPages - 3 && currentPage < totalPages - 4) {
                return <span key={i} className="px-2 text-gray-500">...</span>
              }
              if (!showPage) return null
              
              return (
                <button
                  key={i}
                  onClick={() => goToPage(pageNum)}
                  className={`px-3 py-1 rounded-lg transition-colors ${
                    currentPage === pageNum
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  {pageNum}
                </button>
              )
            })}
          </div>
          
          <button
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
            className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
