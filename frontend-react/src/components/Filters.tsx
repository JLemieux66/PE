import { useState, useEffect } from 'react'
import { Search, Filter, X } from 'lucide-react'
import type { PEFirm, CompanyFilters } from '../types/company'

interface FiltersProps {
  peFirms: PEFirm[]
  industries: string[]
  onFilterChange: (filters: CompanyFilters) => void
}

export default function Filters({ peFirms, industries, onFilterChange }: FiltersProps) {
  const [search, setSearch] = useState('')
  const [selectedFirms, setSelectedFirms] = useState<string[]>([])
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([])
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([])
  const [selectedExitTypes, setSelectedExitTypes] = useState<string[]>([])

  // Apply filters automatically whenever any filter changes
  useEffect(() => {
    const filters: CompanyFilters = {}
    if (search) filters.search = search
    if (selectedFirms.length > 0) filters.pe_firm = selectedFirms.join(',') // Multi-select: comma-separated
    if (selectedStatuses.length > 0) filters.status = selectedStatuses[0]
    if (selectedIndustries.length > 0) filters.industry = selectedIndustries.join(',') // Multi-select: comma-separated
    if (selectedExitTypes.length > 0) filters.exit_type = selectedExitTypes[0]
    onFilterChange(filters)
  }, [search, selectedFirms, selectedStatuses, selectedIndustries, selectedExitTypes, onFilterChange])

  const toggleSelection = (value: string, currentList: string[], setter: (list: string[]) => void) => {
    if (currentList.includes(value)) {
      setter(currentList.filter(item => item !== value))
    } else {
      setter([...currentList, value])
    }
  }

  const handleReset = () => {
    setSearch('')
    setSelectedFirms([])
    setSelectedStatuses([])
    setSelectedIndustries([])
    setSelectedExitTypes([])
  }

  const statuses = ['Active', 'Exit']
  const exitTypes = ['IPO', 'Acquisition']

  return (
    <div className="bg-white rounded-lg shadow p-4 sticky top-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Filter className="w-5 h-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        </div>
        <button
          onClick={handleReset}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center"
        >
          <X className="w-4 h-4 mr-1" />
          Clear All
        </button>
      </div>
      
      <div className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search companies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>

        {/* Multi-select PE Firms */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">PE Firms</label>
          <div className="flex flex-wrap gap-2 max-h-60 overflow-y-auto p-2 border border-gray-200 rounded-lg">
            {peFirms.map((firm) => (
              <button
                key={firm.id}
                onClick={() => toggleSelection(firm.name, selectedFirms, setSelectedFirms)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  selectedFirms.includes(firm.name)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {firm.name} ({firm.total_investments})
              </button>
            ))}
          </div>
          {selectedFirms.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {selectedFirms.map((firm) => (
                <span key={firm} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {firm}
                  <button
                    onClick={() => toggleSelection(firm, selectedFirms, setSelectedFirms)}
                    className="ml-1 hover:text-blue-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
          <div className="space-y-2">
            {statuses.map((status) => (
              <label key={status} className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedStatuses.includes(status)}
                  onChange={() => toggleSelection(status, selectedStatuses, setSelectedStatuses)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">{status}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Exit Types */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Exit Type</label>
          <div className="space-y-2">
            {exitTypes.map((exitType) => (
              <label key={exitType} className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedExitTypes.includes(exitType)}
                  onChange={() => toggleSelection(exitType, selectedExitTypes, setSelectedExitTypes)}
                  disabled={!selectedStatuses.includes('Exit')}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
                />
                <span className="ml-2 text-sm text-gray-700">{exitType}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Industries */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Industries</label>
          <div className="max-h-48 overflow-y-auto space-y-2 border border-gray-200 rounded p-2">
              {industries.map((industry) => (
                <label key={industry} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedIndustries.includes(industry)}
                    onChange={() => toggleSelection(industry, selectedIndustries, setSelectedIndustries)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{industry}</span>
                </label>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}