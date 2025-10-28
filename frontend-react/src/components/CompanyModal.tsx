import { useQuery } from '@tanstack/react-query'
import { fetchCompanyById } from '../api/client'
import { useState } from 'react'

interface CompanyModalProps {
  companyId: number
  onClose: () => void
}

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

export default function CompanyModal({ companyId, onClose }: CompanyModalProps) {
  const [logoError, setLogoError] = useState(false)
  
  const { data: company, isLoading, error } = useQuery({
    queryKey: ['company', companyId],
    queryFn: () => fetchCompanyById(companyId.toString()),
  })

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading company details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !company) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Error</h2>
          <p className="text-gray-600 mb-4">Could not load company details.</p>
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Close
          </button>
        </div>
      </div>
    )
  }

  const domain = extractDomain(company.website)
  const logoUrl = domain ? `https://logo.clearbit.com/${domain}` : null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Company Logo */}
            {logoUrl && !logoError ? (
              <img
                src={logoUrl}
                alt={`${company.name} logo`}
                onError={() => setLogoError(true)}
                className="w-12 h-12 object-contain rounded"
              />
            ) : (
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded flex items-center justify-center text-white font-bold text-lg">
                {getInitials(company.name)}
              </div>
            )}
            <h2 className="text-2xl font-bold text-gray-900">{company.name}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Status and Industry Badges */}
          <div className="flex flex-wrap gap-2">
            {company.status && (
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                company.status === 'Active' 
                  ? 'bg-green-100 text-green-800'
                  : company.status === 'Exited'
                  ? 'bg-gray-100 text-gray-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {company.status}
              </span>
            )}
            
            {company.industry_category && (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {company.industry_category}
              </span>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            {company.website && (
              <a
                href={company.website}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center text-sm"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                Visit Website
              </a>
            )}
            
            {company.linkedin_url && (
              <a
                href={company.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-[#0077B5] text-white rounded-lg hover:bg-[#006399] flex items-center text-sm"
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
                LinkedIn
              </a>
            )}
          </div>

          {/* Description */}
          {company.description && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">About</h3>
              <p className="text-gray-700 leading-relaxed">{company.description}</p>
            </div>
          )}

          {/* Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Company Information */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Company Information</h3>
              <dl className="space-y-2">
                {company.headquarters && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500">Headquarters</dt>
                    <dd className="text-sm text-gray-900">{company.headquarters}</dd>
                  </div>
                )}
                
                {company.investment_year && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500">Investment Year</dt>
                    <dd className="text-sm text-gray-900">{company.investment_year}</dd>
                  </div>
                )}
                
                {company.exit_type && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500">Exit Type</dt>
                    <dd className="text-sm text-gray-900">{company.exit_type}</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Financial Metrics */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Financial Metrics</h3>
              <dl className="space-y-2">
                {company.revenue_range && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500">Revenue Range</dt>
                    <dd className="text-sm text-gray-900">{company.revenue_range}</dd>
                  </div>
                )}
                
                {company.employee_count && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500">Employee Count</dt>
                    <dd className="text-sm text-gray-900">{company.employee_count}</dd>
                  </div>
                )}
                
                {company.predicted_revenue && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500">Predicted Revenue (ML)</dt>
                    <dd className="text-sm text-gray-900">
                      ${(company.predicted_revenue / 1000000).toFixed(1)}M
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>

          {/* PE Firms */}
          {company.pe_firms && company.pe_firms.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Private Equity Firms</h3>
              <div className="flex flex-wrap gap-2">
                {company.pe_firms.map((firm: string, index: number) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-lg text-sm font-medium"
                  >
                    {firm}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full md:w-auto px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
