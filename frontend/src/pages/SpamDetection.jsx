import React, { useState } from 'react'
import axios from 'axios'

const SpamDetection = () => {
  const [text, setText] = useState('')
  const [type, setType] = useState('email')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      const response = await axios.post('/api/spam/predict', {
        text,
        type
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
      <h1 className="text-3xl font-bold mb-6">Spam Detection</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Text Type
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded"
            >
              <option value="email">Email</option>
              <option value="sms">SMS</option>
              <option value="comment">Comment</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Text to Analyze
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows="6"
              className="w-full px-3 py-2 border border-gray-300 rounded"
              placeholder="Enter text to check for spam..."
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Analyzing...' : 'Check for Spam'}
          </button>
        </form>
      </div>

      {result && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold mb-4">Result</h2>
          <div className={`p-4 rounded ${result.is_spam ? 'bg-red-100' : 'bg-green-100'}`}>
            <p className="text-lg font-semibold">
              {result.is_spam ? '⚠️ SPAM DETECTED' : '✅ NOT SPAM'}
            </p>
            <p className="mt-2">Confidence: {(result.confidence * 100).toFixed(2)}%</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default SpamDetection

