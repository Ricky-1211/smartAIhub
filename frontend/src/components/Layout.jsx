import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const Layout = ({ children }) => {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/spam', label: 'Spam Detection', icon: '📧' },
    { path: '/whatsapp', label: 'WhatsApp Analysis', icon: '💬' },
    { path: '/movie', label: 'Movie Recommendation', icon: '🎬' },
    { path: '/resume', label: 'Resume Matcher', icon: '📄' },
    { path: '/house', label: 'House Price', icon: '🏠' },
    { path: '/fraud', label: 'Fraud Detection', icon: '🔒' },
    { path: '/code-review', label: 'Code Review', icon: '💻' },
    { path: '/admin', label: 'Admin Panel', icon: '⚙️' },
  ]

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-gray-800 text-white transition-all duration-300`}>
        <div className="p-4">
          <h1 className={`text-xl font-bold ${sidebarOpen ? '' : 'hidden'}`}>
            SmartAIHub
          </h1>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="mt-2 text-gray-400 hover:text-white"
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>
        <nav className="mt-8">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-4 py-3 hover:bg-gray-700 ${
                location.pathname === item.path ? 'bg-gray-700' : ''
              }`}
            >
              <span className="text-2xl mr-3">{item.icon}</span>
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm p-4 flex justify-between items-center">
          <h2 className="text-2xl font-semibold">
            {menuItems.find(item => item.path === location.pathname)?.label || 'Dashboard'}
          </h2>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">{user?.username || 'User'}</span>
            <button
              onClick={logout}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout

