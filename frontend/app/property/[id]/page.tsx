'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Home, Bed, Bath, DollarSign, MapPin, Calendar, Share2, Heart } from 'lucide-react'
import Link from 'next/link'

interface PropertyDetail {
  id: string
  canonical_key: string
  address: {
    line1: string
    line2?: string
    city: string
    state: string
    postal_code: string
    country: string
  }
  location: {
    latitude?: number
    longitude?: number
  }
  details: {
    property_type: string
    bedrooms?: number
    bathrooms?: number
    sqft?: number
    lot_sqft?: number
    year_built?: number
    description?: string
  }
  status: string
  list_price?: number
  images: string[]
  sources: Array<{
    provider_name: string
    source_url?: string
  }>
  first_seen_at: string
  last_seen_at: string
}

export default function PropertyPage() {
  const params = useParams()
  const router = useRouter()
  const [property, setProperty] = useState<PropertyDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentImageIndex, setCurrentImageIndex] = useState(0)

  useEffect(() => {
    const fetchProperty = async () => {
      try {
        setIsLoading(true)
        setError(null)

        const response = await fetch(`/api/listings/${params.id}`)
        
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Property not found')
          }
          throw new Error(`Failed to fetch property: ${response.statusText}`)
        }

        const data: PropertyDetail = await response.json()
        setProperty(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch property')
      } finally {
        setIsLoading(false)
      }
    }

    if (params.id) {
      fetchProperty()
    }
  }, [params.id])

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

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `${property?.address.line1}, ${property?.address.city}`,
          text: `Check out this property: ${property?.address.line1}, ${property?.address.city}, ${property?.address.state}`,
          url: window.location.href,
        })
      } catch (err) {
        console.log('Error sharing:', err)
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href)
      alert('Link copied to clipboard!')
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading property details...</p>
        </div>
      </div>
    )
  }

  if (error || !property) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p className="font-bold">Error</p>
            <p>{error || 'Property not found'}</p>
          </div>
          <Link href="/search" className="btn-primary">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Search
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Back Button */}
      <div className="mb-6">
        <Link href="/search" className="text-primary-600 hover:text-primary-800 flex items-center">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Search Results
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Images */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            {property.images.length > 0 ? (
              <div>
                <div className="relative">
                  <img
                    src={property.images[currentImageIndex]}
                    alt={`Property image ${currentImageIndex + 1}`}
                    className="w-full h-96 object-cover"
                  />
                  {property.images.length > 1 && (
                    <div className="absolute bottom-4 left-4 right-4 flex justify-between">
                      <button
                        onClick={() => setCurrentImageIndex(Math.max(0, currentImageIndex - 1))}
                        className="bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70"
                        disabled={currentImageIndex === 0}
                      >
                        ←
                      </button>
                      <span className="bg-black bg-opacity-50 text-white px-3 py-1 rounded-full">
                        {currentImageIndex + 1} / {property.images.length}
                      </span>
                      <button
                        onClick={() => setCurrentImageIndex(Math.min(property.images.length - 1, currentImageIndex + 1))}
                        className="bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70"
                        disabled={currentImageIndex === property.images.length - 1}
                      >
                        →
                      </button>
                    </div>
                  )}
                </div>
                {property.images.length > 1 && (
                  <div className="flex p-4 space-x-2 overflow-x-auto">
                    {property.images.map((image, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentImageIndex(index)}
                        className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 ${
                          index === currentImageIndex ? 'border-primary-600' : 'border-gray-300'
                        }`}
                      >
                        <img
                          src={image}
                          alt={`Thumbnail ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="w-full h-96 bg-gray-200 flex items-center justify-center">
                <Home className="w-16 h-16 text-gray-400" />
                <span className="ml-2 text-gray-500">No images available</span>
              </div>
            )}
          </div>

          {/* Property Details */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {property.address.line1}
                </h1>
                <p className="text-lg text-gray-600 flex items-center">
                  <MapPin className="w-4 h-4 mr-1" />
                  {property.address.city}, {property.address.state} {property.address.postal_code}
                </p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={handleShare}
                  className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  title="Share property"
                >
                  <Share2 className="w-5 h-5" />
                </button>
                <button
                  className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  title="Save to favorites"
                >
                  <Heart className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <DollarSign className="w-6 h-6 mx-auto mb-2 text-primary-600" />
                <div className="text-2xl font-bold text-gray-900">
                  {formatPrice(property.list_price)}
                </div>
                <div className="text-sm text-gray-600">List Price</div>
              </div>
              {property.details.bedrooms && (
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <Bed className="w-6 h-6 mx-auto mb-2 text-primary-600" />
                  <div className="text-2xl font-bold text-gray-900">
                    {property.details.bedrooms}
                  </div>
                  <div className="text-sm text-gray-600">Bedrooms</div>
                </div>
              )}
              {property.details.bathrooms && (
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <Bath className="w-6 h-6 mx-auto mb-2 text-primary-600" />
                  <div className="text-2xl font-bold text-gray-900">
                    {property.details.bathrooms}
                  </div>
                  <div className="text-sm text-gray-600">Bathrooms</div>
                </div>
              )}
              {property.details.sqft && (
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <Home className="w-6 h-6 mx-auto mb-2 text-primary-600" />
                  <div className="text-2xl font-bold text-gray-900">
                    {property.details.sqft.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Square Feet</div>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-4 mb-6">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(property.status)}`}>
                {property.status}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                {property.details.property_type.replace('_', ' ')}
              </span>
              {property.details.year_built && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                  <Calendar className="w-3 h-3 mr-1" />
                  Built in {property.details.year_built}
                </span>
              )}
            </div>

            {property.details.description && (
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-3">Description</h2>
                <p className="text-gray-700 leading-relaxed">
                  {property.details.description}
                </p>
              </div>
            )}

            {property.details.lot_sqft && (
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-3">Property Details</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-gray-600">Lot Size:</span>
                    <span className="ml-2 font-medium">{property.details.lot_sqft.toLocaleString()} sq ft</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Property Type:</span>
                    <span className="ml-2 font-medium capitalize">{property.details.property_type.replace('_', ' ')}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Contact Card */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Interested in this property?</h3>
            <button className="w-full btn-primary mb-3">
              Contact Agent
            </button>
            <button className="w-full btn-secondary">
              Schedule Tour
            </button>
          </div>

          {/* Sources */}
          {property.sources.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Listed By</h3>
              <div className="space-y-2">
                {property.sources.map((source, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-gray-700">{source.provider_name}</span>
                    {source.source_url && (
                      <a
                        href={source.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-800 text-sm"
                      >
                        View Source
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Location Info */}
          {property.location.latitude && property.location.longitude && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Location</h3>
              <div className="aspect-square bg-gray-200 rounded-lg flex items-center justify-center">
                <MapPin className="w-8 h-8 text-gray-400" />
                <span className="ml-2 text-gray-500">Map View</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {property.location.latitude.toFixed(6)}, {property.location.longitude.toFixed(6)}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
