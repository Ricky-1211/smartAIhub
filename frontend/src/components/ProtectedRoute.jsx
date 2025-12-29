import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const ProtectedRoute = ({ children }) => {
  const { token, loading } = useAuth()

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return children
}

export default ProtectedRoute

