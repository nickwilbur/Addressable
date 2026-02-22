const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface SearchCriteria {
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
  year_built_min?: number
  year_built_max?: number
}

export interface Listing {
  id: string
  canonical_key: string
  address: {
    line1: string
    city: string
    state: string
    postal_code: string
  }
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

export interface SearchResponse {
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

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Error: ${response.status} - ${errorText}`)
    }

    return response.json()
  }

  async search(criteria: SearchCriteria): Promise<SearchResponse> {
    const params = new URLSearchParams()
    
    Object.entries(criteria).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          params.set(key, value.join(','))
        } else {
          params.set(key, value.toString())
        }
      }
    })

    return this.request<SearchResponse>(`/api/search?${params.toString()}`)
  }

  async getSearchResults(searchQueryId: string, page: number = 1, pageSize: number = 20): Promise<SearchResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })

    return this.request<SearchResponse>(`/api/search/${searchQueryId}?${params.toString()}`)
  }

  async getListing(listingId: string) {
    return this.request(`/api/listings/${listingId}`)
  }

  async getProviders() {
    return this.request('/api/providers')
  }

  async healthCheck() {
    return this.request('/healthz')
  }
}

export const apiClient = new ApiClient()
