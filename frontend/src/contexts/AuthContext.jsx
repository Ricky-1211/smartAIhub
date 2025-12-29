import React, { createContext, useState, useContext, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [token])

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/auth/me')
      setUser(response.data.data)
    } catch (error) {
      localStorage.removeItem('token')
      setToken(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await axios.post('/api/auth/login', formData)
    const { access_token } = response.data
    localStorage.setItem('token', access_token)
    setToken(access_token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    await fetchUser()
    return response.data
  }

  const register = async (userData) => {
    const response = await axios.post('/api/auth/register', userData)
    return response.data
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
    delete axios.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

