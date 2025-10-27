import { useState } from 'react'
import { Search, Filter } from 'lucide-react'
import type { PEFirm, CompanyFilters } from '../types/company'

interface FiltersProps {
  peFirms: PEFirm[]
  onFilterChange: (filters: CompanyFilters) => void
}

export default function Filters({ peFirms, onFilterChange }: FiltersProps) {
  const [search, setSearch] = useState('')
  const [selectedFirm, setSelectedFirm] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [selectedExitType, setSelectedExitType] = useState('')

  const handleFilterChange = () => {
    const filters: CompanyFilters = {}
    if (search) filters.search = search
    if (selectedFirm) filters.pe_firm = selectedFirm
    if (selectedStatus) filters.status = selectedStatus
    if (selectedExitType) filters.exit_type = selectedExitType
    filters.limit = 500
    onFilterChange(filters)
  }

  const handleReset = () => {
    setSearch('')
    setSelectedFirm('')
    setSelectedStatus('')
    setSelectedExitType('')
    onFilterChange({})
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex items-center mb-4">
        <Filter className="w-5 h-5 text-gray-600 mr-2" />
        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search companies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleFilterChange()}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* PE Firm */}
        <select
          value={selectedFirm}
          onChange={(e) => setSelectedFirm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All PE Firms</option>
          {peFirms.map((firm) => (
            <option key={firm.id} value={firm.name}>
              {firm.name} ({firm.total_investments})
            </option>
          ))}
        </select>

        {/* Status */}
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Statuses</option>
          <option value="Active">Active</option>
          <option value="Exit">Exit</option>
        </select>

        {/* Exit Type */}
        <select
          value={selectedExitType}
          onChange={(e) => setSelectedExitType(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={selectedStatus !== 'Exit'}
        >
          <option value="">All Exit Types</option>
          <option value="IPO">IPO</option>
          <option value="Acquisition">Acquisition</option>
        </select>

        {/* Actions */}
        <div className="flex space-x-2">
          <button
            onClick={handleFilterChange}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Apply
          </button>
          <button
            onClick={handleReset}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  )
}
