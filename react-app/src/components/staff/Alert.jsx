import React from 'react'
import { AlertCircle, Info, CheckCircle, AlertTriangle } from 'lucide-react'

export const Alert = ({ type = 'info', children }) => {
  const styles = {
    info: 'bg-blue-50 dark:bg-blue-950 border-blue-600 dark:border-blue-500 text-blue-900 dark:text-blue-100',
    success: 'bg-green-50 dark:bg-green-950 border-green-600 dark:border-green-500 text-green-900 dark:text-green-100',
    danger: 'bg-red-50 dark:bg-red-950 border-red-600 dark:border-red-500 text-red-900 dark:text-red-100',
    warning: 'bg-yellow-50 dark:bg-yellow-950 border-yellow-600 dark:border-yellow-500 text-yellow-900 dark:text-yellow-100',
  }

  const icons = {
    info: <Info className="w-5 h-5" />,
    success: <CheckCircle className="w-5 h-5" />,
    danger: <AlertCircle className="w-5 h-5" />,
    warning: <AlertTriangle className="w-5 h-5" />,
  }

  return (
    <div className={`rounded-lg border-l-4 p-4 flex gap-3 ${styles[type]}`}>
      <div className="flex-shrink-0">{icons[type]}</div>
      <div className="text-sm">{children}</div>
    </div>
  )
}
