import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchCompanyById } from '../api/client'

export default function CompanyDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: company, isLoading, error } = useQuery({
    queryKey: ['company', id],
    queryFn: () => fetchCompanyById(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading company details...</p>
        </div>
      </div>
    )
  }

  if (error || !company) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Company Not Found</h2>
          <p className="text-gray-600 mb-4">The company you're looking for doesn't exist.</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Companies
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header with Back Button */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Companies
          </button>
        </div>

        {/* Company Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{company.name}</h1>
              
              <div className="flex flex-wrap gap-4 mt-4">
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
            </div>

            <div className="flex gap-3 ml-4">
              {company.website && (
                <a
                  href={company.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                  className="px-4 py-2 bg-[#0077B5] text-white rounded-lg hover:bg-[#006399] flex items-center"
                >
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                  </svg>
                  LinkedIn
                </a>
              )}
            </div>
          </div>

          {company.description && (
            <p className="mt-6 text-gray-700 leading-relaxed">{company.description}</p>
          )}
        </div>

        {/* Company Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Basic Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Company Information</h2>
            <dl className="space-y-3">
              {company.headquarters && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Headquarters</dt>
                  <dd className="mt-1 text-sm text-gray-900">{company.headquarters}</dd>
                </div>
              )}
              
              {company.investment_year && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Investment Year</dt>
                  <dd className="mt-1 text-sm text-gray-900">{company.investment_year}</dd>
                </div>
              )}
              
              {company.exit_year && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Exit Year</dt>
                  <dd className="mt-1 text-sm text-gray-900">{company.exit_year}</dd>
                </div>
              )}
              
              {company.exit_type && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Exit Type</dt>
                  <dd className="mt-1 text-sm text-gray-900">{company.exit_type}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Financial Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Financial Metrics</h2>
            <dl className="space-y-3">
              {company.revenue_range && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Revenue Range</dt>
                  <dd className="mt-1 text-sm text-gray-900">{company.revenue_range}</dd>
                </div>
              )}
              
              {company.employee_count && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Employee Count</dt>
                  <dd className="mt-1 text-sm text-gray-900">{company.employee_count}</dd>
                </div>
              )}
              
              {company.predicted_revenue && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Predicted Revenue (ML)</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    ${(company.predicted_revenue / 1000000).toFixed(1)}M
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {/* PE Firms */}
        {company.pe_firms && company.pe_firms.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Private Equity Firms</h2>
            <div className="flex flex-wrap gap-3">
              {company.pe_firms && company.pe_firms.length > 0 && company.pe_firms.map((firm: string, index: number) => (
                <div
                  key={index}
                  className="px-4 py-2 bg-indigo-100 text-indigo-800 rounded-lg font-medium"
                >
                  {firm}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Data Sources */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Data Sources</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <dt className="font-medium text-gray-500">Crunchbase</dt>
              <dd className="mt-1 text-gray-900">
                {company.linkedin_url || company.revenue_range ? '✓ Available' : '✗ Not available'}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500">Website</dt>
              <dd className="mt-1 text-gray-900">
                {company.website ? '✓ Available' : '✗ Not available'}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500">Last Updated</dt>
              <dd className="mt-1 text-gray-900">
                {company.last_updated 
                  ? new Date(company.last_updated).toLocaleDateString()
                  : 'N/A'
                }
              </dd>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
