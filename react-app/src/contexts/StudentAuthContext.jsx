import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import http from '../api/api'

const StudentAuthContext = createContext()

export const StudentAuthProvider = ({ children }) => {
  const [authToken, setAuthToken] = useState(null)
  const [userInfo, setUserInfo] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for stored token on mount
    const token = localStorage.getItem('studentToken')
    const info = localStorage.getItem('studentInfo')
    if (token) {
      setAuthToken(token)
      if (info) {
        setUserInfo(JSON.parse(info))
      }
    }
    setLoading(false)
  }, [])

  const login = async (username, password, registerNumber) => {
    try {
      const response = await http().post('/auth/student/login', {
        username,
        password,
        register_number: registerNumber,
      })

      const { token, user } = response.data
      setAuthToken(token)
      setUserInfo(user)
      localStorage.setItem('studentToken', token)
      localStorage.setItem('studentInfo', JSON.stringify(user))
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed'
      return { success: false, error: message }
    }
  }

  const logout = () => {
    setAuthToken(null)
    setUserInfo(null)
    localStorage.removeItem('studentToken')
    localStorage.removeItem('studentInfo')
  }

  return (
    <StudentAuthContext.Provider
      value={{
        authToken,
        userInfo,
        loading,
        login,
        logout,
      }}
    >
      {children}
    </StudentAuthContext.Provider>
  )
}

export const useStudentAuth = () => {
  const context = useContext(StudentAuthContext)
  if (!context) {
    throw new Error('useStudentAuth must be used within StudentAuthProvider')
  }
  return context
}
