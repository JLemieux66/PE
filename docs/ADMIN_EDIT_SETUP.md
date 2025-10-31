# Admin Edit Functionality Setup Guide

## Overview
Added admin capability to edit company details directly from the frontend.

## Backend Changes (api_v2.py)

### New Endpoints:
1. **PUT /api/companies/{company_id}** - Update company details
2. **DELETE /api/companies/{company_id}** - Delete a company

### Authentication:
Uses header-based API key authentication:
- Header: `X-Admin-Key`
- Value: Set via `ADMIN_API_KEY` environment variable

### Editable Fields:
- name
- website
- linkedin_url
- crunchbase_url
- description
- city, state_region, country
- industry_category
- revenue_range (Crunchbase code)
- employee_count (Crunchbase code)
- is_public, ipo_exchange, ipo_date

## Frontend Component (CompanyEditModal.tsx)

### Features:
- Modal-based edit form
- Only sends changed fields to API
- Form validation
- Loading states and error handling
- React Query integration for cache invalidation

### Configuration:
Set environment variable in your `.env` file:
```
VITE_ADMIN_API_KEY=your-secret-admin-key-here
```

## Setup Steps

### 1. Set Admin API Key on Railway

In your Railway dashboard:
1. Go to your backend service
2. Add environment variable:
   ```
   ADMIN_API_KEY=your-strong-secret-key-here
   ```
3. Redeploy the backend

### 2. Configure Frontend Environment

In `pe-portfolio-react/.env`:
```bash
VITE_API_BASE_URL=https://peportco-production.up.railway.app/api
VITE_ADMIN_API_KEY=your-strong-secret-key-here
```

### 3. Add Edit Button to Company Details

Example usage in your company detail page:

```tsx
import { useState } from 'react';
import { Pencil } from 'lucide-react';
import CompanyEditModal from '../components/CompanyEditModal';

function CompanyDetail({ company }) {
  const [showEditModal, setShowEditModal] = useState(false);
  
  return (
    <div>
      {/* Your existing company details */}
      
      {/* Admin Edit Button */}
      <button
        onClick={() => setShowEditModal(true)}
        className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-md"
      >
        <Pencil className="w-4 h-4" />
        Edit Company
      </button>
      
      {/* Edit Modal */}
      {showEditModal && (
        <CompanyEditModal
          company={company}
          onClose={() => setShowEditModal(false)}
        />
      )}
    </div>
  );
}
```

### 4. Optional: Add Admin Check

To only show edit button for admins:

```tsx
const isAdmin = !!import.meta.env.VITE_ADMIN_API_KEY;

{isAdmin && (
  <button onClick={() => setShowEditModal(true)}>
    <Pencil /> Edit
  </button>
)}
```

## Security Notes

1. **Never commit API keys** - Add `.env` to `.gitignore`
2. **Use strong keys** - Generate with: `openssl rand -hex 32`
3. **HTTPS only** - Railway provides this by default
4. **Rate limiting** - Consider adding to production

## API Examples

### Update Company
```bash
curl -X PUT https://peportco-production.up.railway.app/api/companies/123 \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: your-secret-key" \
  -d '{
    "website": "https://newwebsite.com",
    "description": "Updated description"
  }'
```

### Response
```json
{
  "message": "Company updated successfully",
  "company_id": 123,
  "updated_fields": ["website", "description"]
}
```

## Future Enhancements

1. **Full authentication system** - OAuth, JWT tokens
2. **Audit logging** - Track who changed what and when
3. **Role-based access** - Different permission levels
4. **Bulk editing** - Update multiple companies at once
5. **Change history** - View previous values and rollback

## Troubleshooting

### 403 Forbidden Error
- Check `X-Admin-Key` header is set correctly
- Verify environment variable on Railway matches frontend

### Changes Not Appearing
- Check browser console for errors
- Verify React Query cache is invalidating
- Refresh the page

### CORS Issues
- Backend already configured for `*` origins
- If needed, update `allow_origins` in api_v2.py
