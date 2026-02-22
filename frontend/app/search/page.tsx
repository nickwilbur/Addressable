'use client'

import { useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { ArrowLeft, ExternalLink, Home, Bed, Bath, DollarSign } from 'lucide-react'
import Link from 'next/link'

interface Listing {
  id: string
  canonical_key: string
  address_line1: string
  city: string
  state: string
  postal_code: string
  details: {
    property_type: string
    bedrooms?: number
    bathrooms?: number
    sqft?: number
  }
  status: string
  list_price?: number
  sources: Array<{
    provider_name: string
    source_url?: string
  }>
}

interface SearchResponse {
  items: Listing[]
  pagination: {
    page: number
    page_size: number
    total_items: number
    total_pages: number
  }
  search_summary: {
    status: string
    total_listings: number
    duration_ms?: number
  }
  external_search_links: string[]
}

export default function SearchPage() {
  const searchParams = useSearchParams()
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const performSearch = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Build query string for API
        const params = new URLSearchParams()
        searchParams.forEach((value, key) => {
          params.set(key, value)
        })

        const response = await fetch(`/api/search?${params.toString()}`)
        
        if (!response.ok) {
          throw new Error(`Search failed: ${response.statusText}`)
        }

        const data: SearchResponse = await response.json()
        setSearchResults(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed')
      } finally {
        setIsLoading(false)
      }
    }

    if (searchParams.has('location')) {
      performSearch()
    }
  }, [searchParams])

  const formatPrice = (price?: number) => {
    if (!price) return 'Price not available'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(price)
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'sold':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Searching properties...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p className="font-bold">Search Error</p>
            <p>{error}</p>
          </div>
          <Link href="/" className="btn-primary">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Search
          </Link>
        </div>
      </div>
    )
  }

  if (!searchResults) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p>No search criteria provided.</p>
          <Link href="/" className="btn-primary mt-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Search
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link href="/" className="text-primary-600 hover:text-primary-800 flex items-center mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Search
        </Link>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Search Results
        </h1>
        
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          <span>Location: {searchParams.get('location')}</span>
          <span>•</span>
          <span>{searchResults.pagination.total_items} properties found</span>
          {searchResults.search_summary.duration_ms && (
            <>
              <span>•</span>
              <span>Search took {(searchResults.search_summary.duration_ms / 1000).toFixed(2)}s</span>
            </>
          )}
        </div>
      </div>

      {/* External Search Links */}
      {searchResults.external_search_links.length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-3">Search on External Sites</h2>
          <div className="flex flex-wrap gap-2">
            {searchResults.external_search_links.map((link, index) => {
              const siteName = link.includes('zillow') ? 'Zillow' : 
                             link.includes('redfin') ? 'Redfin' : 
                             link.includes('realtor') ? 'Realtor.com' : 'External Site'
              
              return (
                <a
                  key={index}
                  href={link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary flex items-center text-sm"
                >
                  <ExternalLink className="w-3 h-3 mr-1" />
                  {siteName}
                </a>
              )
            })}
          </div>
        </div>
      )}

      {/* Results */}
      {searchResults.items.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">No properties found matching your criteria.</p>
          <Link href="/" className="btn-primary">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Modify Search
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {searchResults.items.map((listing) => (
            <div key={listing.id} className="card p-6">
              <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start">
                {/* Property Details */}
                <div className="flex-1">
                  <div className="mb-4">
                    <Link href={`/property/${listing.id}`}>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2 hover:text-primary-600 transition-colors">
                        {listing.address_line1}
                      </h3>
                    </Link>
                    <p className="text-gray-600">
                      {listing.city}, {listing.state} {listing.postal_code}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    {listing.details.bedrooms && (
                      <div className="flex items-center text-gray-600">
                        <Bed className="w-4 h-4 mr-1" />
                        {listing.details.bedrooms} bed{listing.details.bedrooms !== 1 ? 's' : ''}
                      </div>
                    )}
                    {listing.details.bathrooms && (
                      <div className="flex items-center text-gray-600">
                        <Bath className="w-4 h-4 mr-1" />
                        {listing.details.bathrooms} bath{listing.details.bathrooms !== 1 ? 's' : ''}
                      </div>
                    )}
                    {listing.details.sqft && (
                      <div className="flex items-center text-gray-600">
                        <span className="w-4 h-4 mr-1">📐</span>
                        {listing.details.sqft.toLocaleString()} sq ft
                      </div>
                    )}
                    <div className="flex items-center">
                      <Home className="w-4 h-4 mr-1 text-gray-600" />
                      <span className="text-gray-600 capitalize">{listing.details.property_type.replace('_', ' ')}</span>
                    </div>
                  </div>

                  {/* Provider Sources */}
                  <div className="flex flex-wrap gap-2">
                    {listing.sources.map((source, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {source.provider_name}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Price and Status */}
                <div className="lg:ml-6 lg:text-right mt-4 lg:mt-0">
                  <div className="mb-2">
                    <div className="text-2xl font-bold text-primary-600">
                      {formatPrice(listing.list_price)}
                    </div>
                  </div>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(listing.status)}`}>
                    {listing.status}
                  </span>
                  <div className="mt-3">
                    <Link href={`/property/${listing.id}`} className="btn-secondary text-sm">
                      View Details
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {searchResults.pagination.total_pages > 1 && (
        <div className="mt-8 flex justify-center">
          <div className="flex items-center space-x-2">
            <span className="text-gray-600">
              Page {searchResults.pagination.page} of {searchResults.pagination.total_pages}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
