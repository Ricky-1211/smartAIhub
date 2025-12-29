import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import SpamDetection from './pages/SpamDetection'
import WhatsAppAnalysis from './pages/WhatsAppAnalysis'
import MovieRecommendation from './pages/MovieRecommendation'
import ResumeMatcher from './pages/ResumeMatcher'
import HousePricePrediction from './pages/HousePricePrediction'
import FraudDetection from './pages/FraudDetection'
import CodeReview from './pages/CodeReview'
import AdminPanel from './pages/AdminPanel'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/spam" element={
            <ProtectedRoute>
              <Layout>
                <SpamDetection />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/whatsapp" element={
            <ProtectedRoute>
              <Layout>
                <WhatsAppAnalysis />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/movie" element={
            <ProtectedRoute>
              <Layout>
                <MovieRecommendation />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/resume" element={
            <ProtectedRoute>
              <Layout>
                <ResumeMatcher />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/house" element={
            <ProtectedRoute>
              <Layout>
                <HousePricePrediction />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/fraud" element={
            <ProtectedRoute>
              <Layout>
                <FraudDetection />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/code-review" element={
            <ProtectedRoute>
              <Layout>
                <CodeReview />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/admin" element={
            <ProtectedRoute>
              <Layout>
                <AdminPanel />
              </Layout>
            </ProtectedRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App

