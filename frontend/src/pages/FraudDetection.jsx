import React, { useState } from 'react'
import axios from 'axios'

const FraudDetection = () => {
  const [formData, setFormData] = useState({
    amount: '',
    user_id: '',
    merchant_id: '',
    transaction_type: 'purchase',
    previous_transactions_count: '0',
    account_age_days: '0'
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
      const response = await axios.post('/api/fraud/detect', {
        amount: parseFloat(formData.amount),
        user_id: formData.user_id,
        merchant_id: formData.merchant_id,
        transaction_type: formData.transaction_type,
        previous_transactions_count: parseInt(formData.previous_transactions_count),
        account_age_days: parseInt(formData.account_age_days)
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
      <h1 className="text-3xl font-bold mb-6">Fraud Detection</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Amount
              </label>
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleChange}
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                User ID
              </label>
              <input
                type="text"
                name="user_id"
                value={formData.user_id}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Merchant ID
              </label>
              <input
                type="text"
                name="merchant_id"
                value={formData.merchant_id}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Transaction Type
              </label>
              <select
                name="transaction_type"
                value={formData.transaction_type}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded"
              >
                <option value="purchase">Purchase</option>
                <option value="withdrawal">Withdrawal</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Previous Transactions Count
              </label>
              <input
                type="number"
                name="previous_transactions_count"
                value={formData.previous_transactions_count}
                onChange={handleChange}
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">
                Account Age (days)
              </label>
              <input
                type="number"
                name="account_age_days"
                value={formData.account_age_days}
                onChange={handleChange}
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Analyzing...' : 'Detect Fraud'}
          </button>
        </form>
      </div>

      {result && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold mb-4">Detection Result</h2>
          <div className={`p-4 rounded ${result.is_fraud ? 'bg-red-100' : 'bg-green-100'}`}>
            <p className="text-lg font-semibold">
              {result.is_fraud ? '⚠️ FRAUD DETECTED' : '✅ SAFE TRANSACTION'}
            </p>
            <p className="mt-2">Fraud Score: {(result.fraud_score * 100).toFixed(2)}%</p>
            <p className="mt-2">Risk Level: <span className="font-bold">{result.risk_level.toUpperCase()}</span></p>
            {result.reasons && result.reasons.length > 0 && (
              <div className="mt-4">
                <p className="font-bold">Reasons:</p>
                <ul className="list-disc list-inside">
                  {result.reasons.map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default FraudDetection

