import React, { useState } from 'react'
import { useStudentAuth } from '../../contexts/StudentAuthContext'
import { useTheme } from '../../contexts/ThemeContext'
import { AlertCircle, LogIn } from 'lucide-react'

export const StudentLoginSection = ({ onLoginSuccess }) => {
  const { login } = useStudentAuth()
  const { isDark } = useTheme()
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    registerNumber: '',
  })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const result = await login(
        formData.username,
        formData.password,
        formData.registerNumber
      )

      if (result.success) {
        setFormData({ username: '', password: '', registerNumber: '' })
        onLoginSuccess?.()
      } else {
        setError(result.error)
      }
    } catch (err) {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`min-h-screen flex items-center justify-center px-4 py-12 ${
      isDark ? 'bg-gray-950' : 'bg-gradient-to-br from-indigo-50 to-purple-50'
    }`}>
      <div className={`w-full max-w-md rounded-2xl shadow-xl overflow-hidden ${
        isDark ? 'bg-gray-900 border border-gray-800' : 'bg-white'
      }`}>
        {/* Header */}
        <div className={`px-6 py-8 text-center ${
          isDark ? 'bg-gradient-to-r from-emerald-600 to-green-600' : 'bg-gradient-to-r from-emerald-600 to-green-600'
        }`}>
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 rounded-lg bg-white bg-opacity-20 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.5 1.5H3a1.5 1.5 0 0 0-1.5 1.5v12a1.5 1.5 0 0 0 1.5 1.5h14a1.5 1.5 0 0 0 1.5-1.5V8.5M10.5 1.5v5h5M10.5 1.5L17 8.5" strokeWidth="2" stroke="white" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-1">Student Portal</h2>
          <p className="text-green-100 text-sm">Access your examination papers</p>
        </div>

        {/* Form */}
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label className={`block text-sm font-semibold mb-2 ${
                isDark ? 'text-gray-300' : 'text-gray-700'
              }`}>
                Moodle Username
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                autoComplete="username"
                onChange={handleChange}
                placeholder="Enter your username"
                required
                className={`w-full px-4 py-2.5 rounded-lg border transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
                  isDark
                    ? 'bg-gray-800 border-gray-700 text-gray-50 placeholder-gray-500 focus:border-emerald-500'
                    : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500 focus:border-emerald-500'
                }`}
              />
            </div>

            {/* Password */}
            <div>
              <label className={`block text-sm font-semibold mb-2 ${
                isDark ? 'text-gray-300' : 'text-gray-700'
              }`}>
                Moodle Password
              </label>
              <input
                type="password"
                name="password"
                autoComplete="current-password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                required
                className={`w-full px-4 py-2.5 rounded-lg border transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
                  isDark
                    ? 'bg-gray-800 border-gray-700 text-gray-50 placeholder-gray-500 focus:border-emerald-500'
                    : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500 focus:border-emerald-500'
                }`}
              />
            </div>

            {/* Register Number */}
            <div>
              <label className={`block text-sm font-semibold mb-2 ${
                isDark ? 'text-gray-300' : 'text-gray-700'
              }`}>
                Register Number
              </label>
              <input
                type="text"
                name="registerNumber"
                value={formData.registerNumber}
                onChange={handleChange}
                placeholder="12-digit number"
                required
                maxLength="12"
                pattern="\d{12}"
                className={`w-full px-4 py-2.5 rounded-lg border transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
                  isDark
                    ? 'bg-gray-800 border-gray-700 text-gray-50 placeholder-gray-500 focus:border-emerald-500'
                    : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500 focus:border-emerald-500'
                }`}
              />
              <small className={`block mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Enter your 12-digit university register number
              </small>
            </div>

            {/* Error Alert */}
            {error && (
              <div className={`p-4 rounded-lg flex gap-3 ${
                isDark ? 'bg-red-950 border border-red-700 text-red-50' : 'bg-red-50 border border-red-200 text-red-900'
              }`}>
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* Security Info */}
            <div className={`p-3 rounded-lg text-sm ${
              isDark ? 'bg-emerald-950 border border-emerald-700 text-emerald-100' : 'bg-emerald-50 border border-emerald-200 text-emerald-900'
            }`}>
              <p className="flex items-start gap-2">
                <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Your credentials are securely used to submit papers. We never store your password.</span>
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2.5 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${
                loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white'
              }`}
            >
              <LogIn className="w-5 h-5" />
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
