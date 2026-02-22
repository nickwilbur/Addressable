import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import SearchForm from '../SearchForm'
import axios from 'axios'

// Mock axios
jest.mock('axios')
const mockedAxios = axios

// Mock next/router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn()
  })
}))

describe('SearchForm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders search form with all fields', () => {
    render(<SearchForm />)
    
    expect(screen.getByLabelText(/location/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/min price/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/max price/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/min beds/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/max beds/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/min baths/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/max baths/i)).toBeInTheDocument()
  })

  test('has correct default values', () => {
    render(<SearchForm />)
    
    const minPriceInput = screen.getByLabelText(/min price/i)
    const maxPriceInput = screen.getByLabelText(/max price/i)
    
    expect(minPriceInput).toHaveValue('')
    expect(maxPriceInput).toHaveValue('1,000,000')
    
    // Check that number inputs exist with correct values
    const allInputs = screen.getAllByRole('spinbutton')
    const numberInputs = allInputs.filter(input => input.getAttribute('type') === 'number')
    
    // Should have beds and baths inputs
    expect(numberInputs.length).toBeGreaterThanOrEqual(4)
    
    // Check for specific values
    const inputsWithValue3 = screen.getAllByDisplayValue('3')
    const inputsWithEmptyValue = screen.getAllByDisplayValue('')
    
    expect(inputsWithValue3.length).toBeGreaterThanOrEqual(2) // max beds and max baths
    expect(inputsWithEmptyValue.length).toBeGreaterThanOrEqual(2) // min beds and min baths
  })

  test('formats price inputs with commas', async () => {
    render(<SearchForm />)
    
    const minPriceInput = screen.getByLabelText(/min price/i)
    
    fireEvent.change(minPriceInput, { target: { value: '500000' } })
    
    await waitFor(() => {
      expect(minPriceInput).toHaveValue('500,000')
    })
  })

  test('shows location suggestions when typing', async () => {
    const mockSuggestions = [
      { city: 'New York', state: 'NY', display_name: 'New York, NY', confidence: 0.9 }
    ]
    
    mockedAxios.get.mockResolvedValue({ data: mockSuggestions })
    
    render(<SearchForm />)
    
    const locationInput = screen.getByLabelText(/location/i)
    
    fireEvent.change(locationInput, { target: { value: 'new' } })
    
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/locations/suggest?query=new&limit=10'
      )
    })
  })
})
