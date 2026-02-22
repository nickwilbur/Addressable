'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Home, DollarSign, Bed, Bath, MapPin } from 'lucide-react'
import axios from 'axios'

interface SearchCriteria {
  location: string
  min_price?: number
  max_price?: number
  bedrooms_min?: number
  bedrooms_max?: number
  bathrooms_min?: number
  bathrooms_max?: number
  sqft_min?: number
  sqft_max?: number
  property_types?: string[]
  status?: string[]
  providers?: string[]
}

interface LocationSuggestion {
  city: string
  state: string
  display_name: string
  confidence?: number
}

export default function SearchForm() {
  const router = useRouter()
  const [isSearching, setIsSearching] = useState(false)
  const [criteria, setCriteria] = useState<SearchCriteria>({
    location: '',
    min_price: 0,
    max_price: 1000000,
    bedrooms_min: 0,
    bedrooms_max: 3,
    bathrooms_min: 0,
    bathrooms_max: 3,
    sqft_min: 0,
    sqft_max: 5000,
    providers: ['realtor'], // Default to realtor
  })
  const [locationSuggestions, setLocationSuggestions] = useState<LocationSuggestion[]>([])
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false)
  const [locationQuery, setLocationQuery] = useState('')
  const locationInputRef = useRef<HTMLInputElement>(null)

  // Format price with commas
  const formatPrice = (value: number | undefined): string => {
    if (value === undefined || value === 0) return ''
    return value.toLocaleString('en-US')
  }

  // Parse price from formatted string
  const parsePrice = (value: string): number | undefined => {
    const cleanValue = value.replace(/,/g, '')
    const parsed = parseInt(cleanValue)
    return isNaN(parsed) ? undefined : parsed
  }

  // Handle location search
  const handleLocationSearch = async (query: string) => {
    setLocationQuery(query)
    setCriteria({ ...criteria, location: query })
    
    if (query.length < 2) {
      setLocationSuggestions([])
      setShowLocationSuggestions(false)
      return
    }

    try {
      const response = await axios.get(`/api/locations/suggest?query=${encodeURIComponent(query)}&limit=10`)
      setLocationSuggestions(response.data)
      setShowLocationSuggestions(true)
    } catch (error) {
      console.error('Location search failed:', error)
      setLocationSuggestions([])
      setShowLocationSuggestions(false)
    }
  }

  // Handle location selection
  const handleLocationSelect = (suggestion: LocationSuggestion) => {
    setCriteria({ ...criteria, location: suggestion.display_name })
    setLocationQuery(suggestion.display_name)
    setShowLocationSuggestions(false)
  }

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (locationInputRef.current && !locationInputRef.current.contains(event.target as Node)) {
        setShowLocationSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!criteria.location.trim()) {
      alert('Please enter a location')
      return
    }

    setIsSearching(true)
    
    try {
      // Build query string for search
      const params = new URLSearchParams()
      params.set('location', criteria.location)
      
      if (criteria.min_price && criteria.min_price > 0) params.set('min_price', criteria.min_price.toString())
      if (criteria.max_price && criteria.max_price > 0) params.set('max_price', criteria.max_price.toString())
      if (criteria.bedrooms_min && criteria.bedrooms_min > 0) params.set('bedrooms_min', criteria.bedrooms_min.toString())
      if (criteria.bedrooms_max && criteria.bedrooms_max > 0) params.set('bedrooms_max', criteria.bedrooms_max.toString())
      if (criteria.bathrooms_min && criteria.bathrooms_min > 0) params.set('bathrooms_min', criteria.bathrooms_min.toString())
      if (criteria.bathrooms_max && criteria.bathrooms_max > 0) params.set('bathrooms_max', criteria.bathrooms_max.toString())
      if (criteria.sqft_min) params.set('sqft_min', criteria.sqft_min.toString())
      if (criteria.sqft_max) params.set('sqft_max', criteria.sqft_max.toString())
      
      // Navigate to search results page
      router.push(`/search?${params.toString()}`)
    } catch (error) {
      console.error('Search error:', error)
      alert('Search failed. Please try again.')
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className="card p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Location */}
        <div className="relative" ref={locationInputRef}>
          <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
            <Home className="inline w-4 h-4 mr-1" />
            Location *
          </label>
          <div className="relative">
            <input
              type="text"
              id="location"
              value={locationQuery}
              onChange={(e) => handleLocationSearch(e.target.value)}
              onFocus={() => locationQuery.length >= 2 && setShowLocationSuggestions(true)}
              placeholder="City, neighborhood, or address"
              className="input-field pr-10"
              required
            />
            <MapPin className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          </div>
          
          {/* Location Suggestions Dropdown */}
          {showLocationSuggestions && locationSuggestions.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
              {locationSuggestions.map((suggestion, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleLocationSelect(suggestion)}
                  className="w-full px-3 py-2 text-left hover:bg-gray-100 flex items-center space-x-2 border-b border-gray-100 last:border-b-0"
                >
                  <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-gray-900">{suggestion.display_name}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Price Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="min_price" className="block text-sm font-medium text-gray-700 mb-2">
              <DollarSign className="inline w-4 h-4 mr-1" />
              Min Price
            </label>
            <input
              type="text"
              id="min_price"
              value={formatPrice(criteria.min_price)}
              onChange={(e) => setCriteria({ ...criteria, min_price: parsePrice(e.target.value) || 0 })}
              placeholder="0"
              className="input-field"
              min="0"
            />
          </div>
          <div>
            <label htmlFor="max_price" className="block text-sm font-medium text-gray-700 mb-2">
              <DollarSign className="inline w-4 h-4 mr-1" />
              Max Price
            </label>
            <input
              type="text"
              id="max_price"
              value={formatPrice(criteria.max_price)}
              onChange={(e) => setCriteria({ ...criteria, max_price: parsePrice(e.target.value) || 0 })}
              placeholder="1,000,000"
              className="input-field"
              min="0"
            />
          </div>
        </div>

        {/* Bedrooms and Bathrooms */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label htmlFor="bedrooms_min" className="block text-sm font-medium text-gray-700 mb-2">
              <Bed className="inline w-4 h-4 mr-1" />
              Min Beds
            </label>
            <input
              type="number"
              id="bedrooms_min"
              value={criteria.bedrooms_min || ''}
              onChange={(e) => setCriteria({ ...criteria, bedrooms_min: e.target.value ? parseInt(e.target.value) : 0 })}
              placeholder="0"
              className="input-field"
              min="0"
              max="10"
            />
          </div>
          <div>
            <label htmlFor="bedrooms_max" className="block text-sm font-medium text-gray-700 mb-2">
              <Bed className="inline w-4 h-4 mr-1" />
              Max Beds
            </label>
            <input
              type="number"
              id="bedrooms_max"
              value={criteria.bedrooms_max || ''}
              onChange={(e) => setCriteria({ ...criteria, bedrooms_max: e.target.value ? parseInt(e.target.value) : 3 })}
              placeholder="3"
              className="input-field"
              min="0"
              max="10"
            />
          </div>
          <div>
            <label htmlFor="bathrooms_min" className="block text-sm font-medium text-gray-700 mb-2">
              <Bath className="inline w-4 h-4 mr-1" />
              Min Baths
            </label>
            <input
              type="number"
              id="bathrooms_min"
              value={criteria.bathrooms_min || ''}
              onChange={(e) => setCriteria({ ...criteria, bathrooms_min: e.target.value ? parseFloat(e.target.value) : 0 })}
              placeholder="0"
              className="input-field"
              min="0"
              max="10"
              step="0.5"
            />
          </div>
          <div>
            <label htmlFor="bathrooms_max" className="block text-sm font-medium text-gray-700 mb-2">
              <Bath className="inline w-4 h-4 mr-1" />
              Max Baths
            </label>
            <input
              type="number"
              id="bathrooms_max"
              value={criteria.bathrooms_max || ''}
              onChange={(e) => setCriteria({ ...criteria, bathrooms_max: e.target.value ? parseFloat(e.target.value) : 3 })}
              placeholder="3"
              className="input-field"
              min="0"
              max="10"
              step="0.5"
            />
          </div>
        </div>

        {/* Square Footage */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="sqft_min" className="block text-sm font-medium text-gray-700 mb-2">
              Min Sq Ft
            </label>
            <input
              type="number"
              id="sqft_min"
              value={criteria.sqft_min || ''}
              onChange={(e) => setCriteria({ ...criteria, sqft_min: e.target.value ? parseInt(e.target.value) : undefined })}
              placeholder="No minimum"
              className="input-field"
              min="0"
            />
          </div>
          <div>
            <label htmlFor="sqft_max" className="block text-sm font-medium text-gray-700 mb-2">
              Max Sq Ft
            </label>
            <input
              type="number"
              id="sqft_max"
              value={criteria.sqft_max || ''}
              onChange={(e) => setCriteria({ ...criteria, sqft_max: e.target.value ? parseInt(e.target.value) : undefined })}
              placeholder="No maximum"
              className="input-field"
              min="0"
            />
          </div>
        </div>

        {/* Provider Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Home className="inline w-4 h-4 mr-1" />
            Search Provider
          </label>
          <div className="space-y-2">
            {['realtor', 'redfin', 'zillow'].map((provider) => (
              <label key={provider} className="flex items-center">
                <input
                  type="radio"
                  name="provider"
                  checked={criteria.providers?.[0] === provider}
                  onChange={() => setCriteria({ ...criteria, providers: [provider] })}
                  className="border-gray-300 text-primary-600 focus:ring-primary-500 mr-2"
                />
                <span className="text-gray-700 capitalize">{provider}</span>
              </label>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-1">Select one real estate website to search</p>
        </div>

        {/* Submit Button */}
        <div className="flex justify-center">
          <button
            type="submit"
            disabled={isSearching || !criteria.location.trim() || !criteria.providers?.length}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <Search className="w-4 h-4 mr-2" />
            {isSearching ? 'Searching...' : 'Search Properties'}
          </button>
        </div>
      </form>
    </div>
  )
}
