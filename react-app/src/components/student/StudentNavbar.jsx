import React from 'react'
import { useStudentAuth } from '../../contexts/StudentAuthContext'
import { useTheme } from '../../contexts/ThemeContext'
import { LogOut, Bell, Settings, Sun, Moon } from 'lucide-react'

export const StudentNavbar = ({ pollInterval, onPollIntervalChange, reportCount }) => {
  const { userInfo, logout } = useStudentAuth()
  const { isDark, toggleTheme } = useTheme()
  const [showPollSettings, setShowPollSettings] = React.useState(false)

  const handlePollChange = (value) => {
    onPollIntervalChange?.(value)
    setShowPollSettings(false)
  }

  const handleLogout = () => {
    logout()
  }

  return (
    <nav className={`sticky top-0 z-50 border-b transition-colors ${
      isDark
        ? 'bg-gray-900 border-gray-800 shadow-lg'
        : 'bg-white border-gray-200 shadow-sm'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-green-600">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.5 1.5H3a1.5 1.5 0 0 0-1.5 1.5v12a1.5 1.5 0 0 0 1.5 1.5h14a1.5 1.5 0 0 0 1.5-1.5V8.5M10.5 1.5v5h5M10.5 1.5L17 8.5" strokeWidth="2" stroke="white" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <span className={`font-bold text-lg hidden sm:inline ${
              isDark ? 'text-gray-50' : 'text-gray-900'
            }`}>
              Student Portal
            </span>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* User Info - Hidden on mobile */}
            <div className={`hidden md:flex items-center gap-2 px-3 py-2 rounded-lg ${
              isDark ? 'bg-gray-800' : 'bg-gray-50'
            }`}>
              <svg className="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
              </svg>
              <span className={`text-sm font-semibold ${
                isDark ? 'text-gray-300' : 'text-gray-700'
              }`}>
                {userInfo?.username || 'Student'}
              </span>
            </div>

            {/* Reports Button */}
            <div className="relative">
              <button className={`p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors relative ${
                isDark ? 'text-gray-300' : 'text-gray-600'
              }`}>
                <Bell className="w-5 h-5" />
                {reportCount > 0 && (
                  <span className="absolute top-0 right-0 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-semibold">
                    {reportCount > 9 ? '9+' : reportCount}
                  </span>
                )}
              </button>
            </div>

            {/* Poll Interval Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowPollSettings(!showPollSettings)}
                className={`p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${
                  isDark ? 'text-gray-300' : 'text-gray-600'
                }`}
              >
                <Settings className="w-5 h-5" />
              </button>
              {showPollSettings && (
                <div className={`absolute right-0 mt-2 w-48 rounded-lg shadow-lg z-50 ${
                  isDark ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
                }`}>
                  <div className="p-3">
                    <p className={`text-sm font-semibold mb-3 ${
                      isDark ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      Report Poll Interval
                    </p>
                    <div className="space-y-2">
                      {[10000, 30000, 60000].map(interval => (
                        <label key={interval} className={`flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-gray-700 ${
                          isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
                        }`}>
                          <input
                            type="radio"
                            name="pollInterval"
                            value={interval}
                            checked={pollInterval === interval}
                            onChange={(e) => handlePollChange(parseInt(e.target.value))}
                            className="w-4 h-4"
                          />
                          <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                            {interval / 1000} seconds
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${
                isDark ? 'text-gray-300' : 'text-gray-600'
              }`}
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white transition-colors text-sm font-semibold"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
