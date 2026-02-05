import React from 'react'
import { Loader } from 'lucide-react'

export const LoadingOverlay = ({ show }) => {
  if (!show) return null

  return (
    <div className="fixed inset-0 bg-white dark:bg-gray-950 bg-opacity-95 dark:bg-opacity-95 flex items-center justify-center z-50">
      <div className="text-center">
        <Loader className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Processing...</p>
      </div>
    </div>
  )
}
