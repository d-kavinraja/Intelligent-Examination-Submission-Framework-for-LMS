import React from 'react'
import { LogOut, User, Sun, Moon } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { useTheme } from '../../contexts/ThemeContext'

export const Navbar = () => {
  const { userName, logout } = useAuth()
  const { isDark, toggleTheme } = useTheme()

  return (
    <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-sm mb-6 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2">
            <img 
              src="https://saveetha.ac.in/wp-content/uploads/2024/03/sec-logo-01as.png" 
              alt="Saveetha Logo" 
              className="h-16"
            />
          </a>

          {/* Right Section */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 transition-colors"
              aria-label="Toggle theme"
              title={isDark ? 'Light mode' : 'Dark mode'}
            >
              {isDark ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>

            {/* User Info and Logout */}
            {userName && (
              <>
                <div className="hidden sm:flex items-center gap-2 text-gray-700 dark:text-gray-300">
                  <User className="w-5 h-5 text-primary-600" />
                  <span className="font-semibold text-sm">{userName}</span>
                </div>
                <button
                  onClick={logout}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg border-2 border-red-300 text-red-600 hover:bg-red-600 hover:text-white hover:border-red-600 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-600 transition-all text-sm font-semibold"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
