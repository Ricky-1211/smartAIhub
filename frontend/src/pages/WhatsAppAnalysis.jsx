import React, { useState } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts'

const WhatsAppAnalysis = () => {
  const [chatText, setChatText] = useState('')
  const [images, setImages] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files)
    const imagePromises = files.map(file => {
      return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (event) => {
          resolve(event.target.result)
        }
        reader.readAsDataURL(file)
      })
    })
    
    Promise.all(imagePromises).then(base64Images => {
      setImages([...images, ...base64Images])
    })
  }

  const removeImage = (index) => {
    setImages(images.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      const response = await axios.post('/api/whatsapp/analyze', {
        chat_text: chatText,
        images: images.length > 0 ? images : undefined
      })
      setResult(response.data.data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">WhatsApp Chat Analysis</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Paste WhatsApp Chat Export
            </label>
            <textarea
              value={chatText}
              onChange={(e) => setChatText(e.target.value)}
              rows="10"
              className="w-full px-3 py-2 border border-gray-300 rounded"
              placeholder="Paste your WhatsApp chat export here..."
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Upload Images (Photos with text will be analyzed)
            </label>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageUpload}
              className="w-full px-3 py-2 border border-gray-300 rounded"
            />
            {images.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {images.map((img, index) => (
                  <div key={index} className="relative">
                    <img
                      src={img}
                      alt={`Upload ${index + 1}`}
                      className="w-20 h-20 object-cover rounded border"
                    />
                    <button
                      type="button"
                      onClick={() => removeImage(index)}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Analyzing...' : 'Analyze Chat'}
          </button>
        </form>
      </div>

      {result && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-4">Overview</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-100 p-4 rounded">
                <p className="text-sm text-gray-600">Total Messages</p>
                <p className="text-2xl font-bold">{result.total_messages}</p>
              </div>
              <div className="bg-green-100 p-4 rounded">
                <p className="text-sm text-gray-600">Participants</p>
                <p className="text-2xl font-bold">{result.total_participants}</p>
              </div>
              <div className="bg-purple-100 p-4 rounded">
                <p className="text-sm text-gray-600">Most Active</p>
                <p className="text-2xl font-bold">{result.most_active_user}</p>
              </div>
            </div>
          </div>

          {result.sentiment_analysis && (
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-2xl font-bold mb-4">Sentiment Analysis</h2>
              <p>Polarity: {result.sentiment_analysis.polarity.toFixed(2)}</p>
              <p>Label: {result.sentiment_analysis.label}</p>
            </div>
          )}

          {result.word_frequency && Object.keys(result.word_frequency).length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-2xl font-bold mb-4">Top Words</h2>
              <BarChart width={600} height={300} data={
                Object.entries(result.word_frequency).slice(0, 10).map(([word, count]) => ({
                  word,
                  count
                }))
              }>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="word" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default WhatsAppAnalysis

