import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import http from '../api/api'

const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
  const [authToken, setAuthToken] = useState(null)
  const [userName, setUserName] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('authToken')
    const user = localStorage.getItem('userName')
    
    if (token && user) {
      setAuthToken(token)
      setUserName(user)
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)

    const response = await http().post('/auth/staff/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    if (response.data.access_token) {
      const token = response.data.access_token
      setAuthToken(token)
      setUserName(username)
      localStorage.setItem('authToken', token)
      localStorage.setItem('userName', username)
      return { success: true }
    }

    return { success: false, error: response.data.detail || 'Login failed' }
  }

  const logout = () => {
    setAuthToken(null)
    setUserName(null)
    localStorage.removeItem('authToken')
    localStorage.removeItem('userName')
  }

  return (
    <AuthContext.Provider value={{ authToken, userName, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
