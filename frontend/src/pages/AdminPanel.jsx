import React, { useState, useEffect } from 'react'
import axios from 'axios'

const AdminPanel = () => {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchStats()
    fetchRecentLogs()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/logging/logs/stats')
      setStats(response.data.data)
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const fetchRecentLogs = async () => {
    setLoading(true)
    try {
      const response = await axios.post('/api/logging/logs/query', {
        limit: 50
      })
      setLogs(response.data.data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Admin Panel</h1>
      
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-md">
            <p className="text-sm text-gray-600">Total Logs</p>
            <p className="text-2xl font-bold">{stats.total_logs}</p>
          </div>
          {stats.by_level && Object.entries(stats.by_level).map(([level, count]) => (
            <div key={level} className="bg-white p-4 rounded-lg shadow-md">
              <p className="text-sm text-gray-600">{level}</p>
              <p className="text-2xl font-bold">{count}</p>
            </div>
          ))}
        </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-4">Recent Logs</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Service</th>
                  <th className="text-left p-2">Level</th>
                  <th className="text-left p-2">Message</th>
                  <th className="text-left p-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b">
                    <td className="p-2">{log.service_name}</td>
                    <td className="p-2">
                      <span className={`px-2 py-1 rounded text-sm ${
                        log.level === 'ERROR' ? 'bg-red-200' :
                        log.level === 'WARNING' ? 'bg-yellow-200' : 'bg-blue-200'
                      }`}>
                        {log.level}
                      </span>
                    </td>
                    <td className="p-2">{log.message}</td>
                    <td className="p-2 text-sm text-gray-600">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminPanel

