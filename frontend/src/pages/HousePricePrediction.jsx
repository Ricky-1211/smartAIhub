import React, { useState } from 'react'
import axios from 'axios'

const HousePricePrediction = () => {
  const [formData, setFormData] = useState({
    area: '',
    bedrooms: '',
    bathrooms: '',
    city: '',
    state: '',
    area_name: '',
    location_score: '5',
    age: '0',
    floor: '1'
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      const response = await axios.post('/api/house/predict', {
        area: parseFloat(formData.area),
        bedrooms: parseInt(formData.bedrooms),
        bathrooms: parseFloat(formData.bathrooms),
        city: formData.city || undefined,
        state: formData.state || undefined,
        area_name: formData.area_name || undefined,
        location_score: parseFloat(formData.location_score),
        age: parseInt(formData.age),
        floor: parseInt(formData.floor)
      })
      setResult(response.data.data || response.data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">House Price Prediction</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Area (sq ft)
              </label>
              <input
                type="number"
                name="area"
                value={formData.area}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Bedrooms
              </label>
              <input
                type="number"
                name="bedrooms"
                value={formData.bedrooms}
                onChange={handleChange}
                min="1"
                className="w-full px-3 py-2 border border-gray-300 rounded"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Bathrooms
              </label>
              <input
                type="number"
                name="bathrooms"
                value={formData.bathrooms}
                onChange={handleChange}
                min="1"
                step="0.5"
                className="w-full px-3 py-2 border border-gray-300 rounded"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                City
              </label>
              <input
                type="text"
                name="city"
                value={formData.city}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded"
                placeholder="e.g., Mumbai, Delhi, Bangalore"
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                State
              </label>
              <input
                type="text"
                name="state"
                value={formData.state}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded"
                placeholder="e.g., Maharashtra, Delhi, Karnataka"
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Area/Neighborhood
              </label>
              <input
                type="text"
                name="area_name"
                value={formData.area_name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded"
                placeholder="e.g., Bandra, Koramangala"
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Location Score (1-10)
              </label>
              <input
                type="number"
                name="location_score"
                value={formData.location_score}
                onChange={handleChange}
                min="1"
                max="10"
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Age (years)
              </label>
              <input
                type="number"
                name="age"
                value={formData.age}
                onChange={handleChange}
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Floor
              </label>
              <input
                type="number"
                name="floor"
                value={formData.floor}
                onChange={handleChange}
                min="1"
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Predicting...' : 'Predict Price'}
          </button>
        </form>
      </div>

      {result && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-4">Prediction Result</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="bg-green-100 p-4 rounded">
                <p className="text-sm text-gray-600">Predicted Price</p>
                <p className="text-4xl font-bold">₹{result.predicted_price.toLocaleString()}</p>
              </div>
              
              {result.predicted_rent && (
                <div className="bg-blue-100 p-4 rounded">
                  <p className="text-sm text-gray-600">Estimated Monthly Rent</p>
                  <p className="text-4xl font-bold">₹{result.predicted_rent.toLocaleString()}</p>
                </div>
              )}
            </div>

            {result.confidence_interval && (
              <div className="mt-4">
                <p className="text-sm text-gray-600">
                  Confidence Interval: ₹{result.confidence_interval.lower.toLocaleString()} - 
                  ₹{result.confidence_interval.upper.toLocaleString()}
                </p>
              </div>
            )}

            {result.location_info && (
              <div className="mt-4 p-4 bg-gray-50 rounded">
                <h3 className="font-bold mb-2">Location Information</h3>
                <p className="text-sm">
                  {result.location_info.city && <span>City: {result.location_info.city}</span>}
                  {result.location_info.state && <span className="ml-2">State: {result.location_info.state}</span>}
                  {result.location_info.area && <span className="ml-2">Area: {result.location_info.area}</span>}
                </p>
                {result.location_info.location_multiplier && (
                  <p className="text-sm text-gray-600 mt-1">
                    Location Multiplier: {result.location_info.location_multiplier.toFixed(2)}x
                  </p>
                )}
              </div>
            )}
          </div>

          {result.suggested_areas && result.suggested_areas.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-2xl font-bold mb-4">Suggested Areas</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.suggested_areas.map((area, index) => (
                  <div key={index} className="border p-4 rounded hover:shadow-lg transition">
                    <h3 className="font-bold text-lg mb-2">{area.name}</h3>
                    <p className="text-green-600 font-semibold">
                      ₹{area.estimated_price.toLocaleString()}
                    </p>
                    <p className="text-blue-600 text-sm">
                      Rent: ₹{area.estimated_rent.toLocaleString()}/month
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Price Multiplier: {area.price_multiplier.toFixed(2)}x
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default HousePricePrediction

