import React from 'react'
import { Link } from 'react-router-dom'

const Dashboard = () => {
  const services = [
    { path: '/spam', name: 'Spam Detection', icon: '📧', description: 'Detect spam in emails, SMS, and comments' },
    { path: '/whatsapp', name: 'WhatsApp Analysis', icon: '💬', description: 'Analyze chat sentiment and activity' },
    { path: '/movie', name: 'Movie Recommendation', icon: '🎬', description: 'Get personalized movie recommendations' },
    { path: '/resume', name: 'Resume Matcher', icon: '📄', description: 'Match resumes with job descriptions' },
    { path: '/house', name: 'House Price Prediction', icon: '🏠', description: 'Predict house prices using ML' },
    { path: '/fraud', name: 'Fraud Detection', icon: '🔒', description: 'Detect fraudulent transactions' },
    { path: '/code-review', name: 'Code Review', icon: '💻', description: 'Automated code quality checks' },
    { path: '/admin', name: 'Admin Panel', icon: '⚙️', description: 'System monitoring and management' },
  ]

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Welcome to SmartAIHub</h1>
      <p className="text-gray-600 mb-8">
        A unified platform for AI services and system utilities
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {services.map((service) => (
          <Link
            key={service.path}
            to={service.path}
            className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow"
          >
            <div className="text-4xl mb-4">{service.icon}</div>
            <h2 className="text-xl font-semibold mb-2">{service.name}</h2>
            <p className="text-gray-600">{service.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}

export default Dashboard

