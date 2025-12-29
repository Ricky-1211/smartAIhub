import React, { useState } from 'react'
import axios from 'axios'

const CodeReview = () => {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      const response = await axios.post('/api/code-review/review', {
        code,
        language
      })
      setResult(response.data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Code Review Automation</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded"
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Code
            </label>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              rows="15"
              className="w-full px-3 py-2 border border-gray-300 rounded font-mono"
              placeholder="Paste your code here..."
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Reviewing...' : 'Review Code'}
          </button>
        </form>
      </div>

      {result && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold mb-4">Review Results</h2>
          
          <div className="mb-4">
            <div className={`p-4 rounded ${
              result.score >= 80 ? 'bg-green-100' :
              result.score >= 60 ? 'bg-yellow-100' : 'bg-red-100'
            }`}>
              <p className="text-sm text-gray-600">Code Quality Score</p>
              <p className="text-4xl font-bold">{result.score}/100</p>
            </div>
          </div>

          {result.metrics && (
            <div className="mb-4">
              <h3 className="font-bold mb-2">Code Metrics</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Total Lines</p>
                  <p className="text-xl font-bold">{result.metrics.total_lines}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Functions</p>
                  <p className="text-xl font-bold">{result.metrics.functions}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Classes</p>
                  <p className="text-xl font-bold">{result.metrics.classes}</p>
                </div>
              </div>
            </div>
          )}

          {result.issues && result.issues.length > 0 && (
            <div className="mb-4">
              <h3 className="font-bold mb-2">Issues Found ({result.issues.length})</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {result.issues.map((issue, i) => (
                  <div key={i} className="border p-3 rounded">
                    <div className="flex justify-between">
                      <span className={`px-2 py-1 rounded text-sm ${
                        issue.severity === 'high' ? 'bg-red-200' :
                        issue.severity === 'medium' ? 'bg-yellow-200' : 'bg-blue-200'
                      }`}>
                        {issue.severity.toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-600">Line {issue.line}</span>
                    </div>
                    <p className="mt-2">{issue.message}</p>
                    {issue.suggestion && (
                      <p className="mt-1 text-sm text-gray-600">💡 {issue.suggestion}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.suggestions && result.suggestions.length > 0 && (
            <div>
              <h3 className="font-bold mb-2">Suggestions</h3>
              <ul className="list-disc list-inside">
                {result.suggestions.map((suggestion, i) => (
                  <li key={i}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default CodeReview

