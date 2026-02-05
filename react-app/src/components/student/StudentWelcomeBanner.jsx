import React from 'react'
import { useTheme } from '../../contexts/ThemeContext'

export const StudentWelcomeBanner = ({ studentName, stats }) => {
  const { isDark } = useTheme()

  return (
    <div className={`rounded-2xl border p-6 mb-6 ${
      isDark
        ? 'bg-gradient-to-r from-gray-900 to-gray-800 border-gray-700'
        : 'bg-gradient-to-r from-white to-gray-50 border-gray-200'
    }`}>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div className="mb-4 md:mb-0">
          <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-gray-50' : 'text-gray-900'}`}>
            👋 Welcome, <span className="text-emerald-600">{studentName}</span>!
          </h2>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            View and submit your examination answer sheets
          </p>
        </div>

        {/* Stats */}
        <div className="flex gap-4">
          <div className={`text-center px-4 py-3 rounded-lg ${
            isDark ? 'bg-gray-800' : 'bg-white border border-gray-200'
          }`}>
            <div className="text-2xl font-bold text-emerald-600">{stats.total}</div>
            <div className={`text-xs font-semibold ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Total Papers
            </div>
          </div>
          <div className={`text-center px-4 py-3 rounded-lg ${
            isDark ? 'bg-gray-800' : 'bg-white border border-gray-200'
          }`}>
            <div className="text-2xl font-bold text-amber-600">{stats.pending}</div>
            <div className={`text-xs font-semibold ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Pending
            </div>
          </div>
          <div className={`text-center px-4 py-3 rounded-lg ${
            isDark ? 'bg-gray-800' : 'bg-white border border-gray-200'
          }`}>
            <div className="text-2xl font-bold text-green-600">{stats.submitted}</div>
            <div className={`text-xs font-semibold ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Submitted
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
