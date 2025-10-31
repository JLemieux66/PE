import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface Company {
  id: number;
  name: string;
  website?: string;
  linkedin_url?: string;
  crunchbase_url?: string;
  description?: string;
  headquarters?: string;
  industry_category?: string;
  revenue_range?: string;
  employee_count?: string;
  is_public?: boolean;
  stock_exchange?: string;
}

interface CompanyEditModalProps {
  company: Company;
  onClose: () => void;
}

const ADMIN_API_KEY = import.meta.env.VITE_ADMIN_API_KEY || '';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://peportco-production.up.railway.app/api';

export default function CompanyEditModal({ company, onClose }: CompanyEditModalProps) {
  const queryClient = useQueryClient();
  
  const [formData, setFormData] = useState({
    name: company.name || '',
    website: company.website || '',
    linkedin_url: company.linkedin_url || '',
    crunchbase_url: company.crunchbase_url || '',
    description: company.description || '',
    city: company.headquarters?.split(',')[0]?.trim() || '',
    industry_category: company.industry_category || '',
    revenue_range: company.revenue_range || '',
    employee_count: company.employee_count || '',
    is_public: company.is_public || false,
    ipo_exchange: company.stock_exchange || '',
  });

  const updateMutation = useMutation({
    mutationFn: async (data: any) => {
      console.log('Sending PUT request:', {
        url: `${API_BASE_URL}/companies/${company.id}`,
        adminKey: ADMIN_API_KEY ? 'Present' : 'Missing',
        data
      });
      
      const response = await fetch(`${API_BASE_URL}/companies/${company.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Key': ADMIN_API_KEY,
        },
        body: JSON.stringify(data),
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const error = await response.json();
        console.error('Error response:', error);
        throw new Error(error.detail || 'Failed to update company');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      queryClient.invalidateQueries({ queryKey: ['company', company.id] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Only send fields that changed
    const updates: any = {};
    Object.keys(formData).forEach((key) => {
      const typedKey = key as keyof typeof formData;
      if (formData[typedKey] !== (company as any)[typedKey]) {
        updates[key] = formData[typedKey];
      }
    });

    if (Object.keys(updates).length > 0) {
      updateMutation.mutate(updates);
    } else {
      onClose();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Edit Company</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Company Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Company Name *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Website */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Website
            </label>
            <input
              type="url"
              name="website"
              value={formData.website}
              onChange={handleChange}
              placeholder="https://example.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* LinkedIn URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              LinkedIn URL
            </label>
            <input
              type="url"
              name="linkedin_url"
              value={formData.linkedin_url}
              onChange={handleChange}
              placeholder="https://linkedin.com/company/example"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Crunchbase URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Crunchbase URL
            </label>
            <input
              type="url"
              name="crunchbase_url"
              value={formData.crunchbase_url}
              onChange={handleChange}
              placeholder="https://www.crunchbase.com/organization/example"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* City */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              City (Headquarters)
            </label>
            <input
              type="text"
              name="city"
              value={formData.city}
              onChange={handleChange}
              placeholder="e.g., San Francisco"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Industry Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Industry Category
            </label>
            <select
              name="industry_category"
              value={formData.industry_category}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Industry</option>
              <option value="Technology & Software">Technology & Software</option>
              <option value="Financial Services">Financial Services</option>
              <option value="Healthcare & Biotech">Healthcare & Biotech</option>
              <option value="E-commerce & Retail">E-commerce & Retail</option>
              <option value="Media & Entertainment">Media & Entertainment</option>
              <option value="Marketing & Advertising">Marketing & Advertising</option>
              <option value="Education & HR">Education & HR</option>
              <option value="Manufacturing & Industrial">Manufacturing & Industrial</option>
              <option value="Energy & Sustainability">Energy & Sustainability</option>
              <option value="Transportation & Automotive">Transportation & Automotive</option>
              <option value="Real Estate & Construction">Real Estate & Construction</option>
              <option value="Communication & Collaboration">Communication & Collaboration</option>
              <option value="Artificial Intelligence & Data">Artificial Intelligence & Data</option>
              <option value="Blockchain & Crypto">Blockchain & Crypto</option>
              <option value="Consulting & Services">Consulting & Services</option>
              <option value="Legal & Compliance">Legal & Compliance</option>
              <option value="Government & Public Sector">Government & Public Sector</option>
              <option value="Agriculture & Food">Agriculture & Food</option>
              <option value="Other">Other</option>
            </select>
          </div>

          {/* Revenue Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Revenue Range
            </label>
            <select
              name="revenue_range"
              value={formData.revenue_range}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Revenue Range</option>
              <option value="Less than $1M">Less than $1M</option>
              <option value="$1M - $10M">$1M - $10M</option>
              <option value="$10M - $50M">$10M - $50M</option>
              <option value="$50M - $100M">$50M - $100M</option>
              <option value="$100M - $500M">$100M - $500M</option>
              <option value="$500M - $1B">$500M - $1B</option>
              <option value="$1B - $10B">$1B - $10B</option>
              <option value="$10B+">$10B+</option>
            </select>
          </div>

          {/* Employee Count */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Employee Count
            </label>
            <select
              name="employee_count"
              value={formData.employee_count}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Employee Count</option>
              <option value="1-10">1-10</option>
              <option value="11-50">11-50</option>
              <option value="51-100">51-100</option>
              <option value="101-250">101-250</option>
              <option value="251-500">251-500</option>
              <option value="501-1,000">501-1,000</option>
              <option value="1,001-5,000">1,001-5,000</option>
              <option value="5,001-10,000">5,001-10,000</option>
              <option value="10,001+">10,001+</option>
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Company description..."
            />
          </div>

          {/* Public Status */}
          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_public"
              checked={formData.is_public}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label className="ml-2 text-sm text-gray-700">
              Publicly Traded (IPO)
            </label>
          </div>

          {/* Stock Exchange (if public) */}
          {formData.is_public && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stock Exchange
              </label>
              <input
                type="text"
                name="ipo_exchange"
                value={formData.ipo_exchange}
                onChange={handleChange}
                placeholder="e.g., NYSE, NASDAQ"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {/* Error Message */}
          {updateMutation.isError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {updateMutation.error instanceof Error ? updateMutation.error.message : 'Failed to update company'}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-300 transition-colors"
            >
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
