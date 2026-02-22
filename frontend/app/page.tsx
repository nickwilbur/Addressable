import Link from 'next/link'
import SearchForm from '@/components/SearchForm'

export default function Home() {
  return (
    <main className="container mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Addressable
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Search properties from multiple data providers in one place
        </p>
      </div>

      <div className="max-w-2xl mx-auto">
        <SearchForm />
      </div>

      <div className="mt-12 text-center">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          How it works
        </h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="text-center">
            <div className="bg-primary-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
              <span className="text-primary-600 font-bold">1</span>
            </div>
            <h3 className="font-semibold mb-2">Enter Search Criteria</h3>
            <p className="text-gray-600">
              Specify location, price range, and property preferences
            </p>
          </div>
          <div className="text-center">
            <div className="bg-primary-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
              <span className="text-primary-600 font-bold">2</span>
            </div>
            <h3 className="font-semibold mb-2">Search Multiple Sources</h3>
            <p className="text-gray-600">
              We query multiple providers simultaneously for comprehensive results
            </p>
          </div>
          <div className="text-center">
            <div className="bg-primary-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
              <span className="text-primary-600 font-bold">3</span>
            </div>
            <h3 className="font-semibold mb-2">Get Unified Results</h3>
            <p className="text-gray-600">
              View deduplicated listings with source attribution and external links
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
