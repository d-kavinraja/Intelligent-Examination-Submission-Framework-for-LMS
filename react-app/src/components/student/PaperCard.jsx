import React from 'react'
import { useTheme } from '../../contexts/ThemeContext'
import { FileText, Eye, Flag, Upload } from 'lucide-react'

export const PaperCard = ({ paper, onView, onSubmit, onReport }) => {
  const { isDark } = useTheme()

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'submitted':
        return {
          bg: isDark ? 'bg-green-950' : 'bg-green-50',
          border: isDark ? 'border-green-700' : 'border-green-200',
          text: isDark ? 'text-green-100' : 'text-green-800',
          badge: 'bg-green-600'
        }
      case 'pending':
        return {
          bg: isDark ? 'bg-amber-950' : 'bg-amber-50',
          border: isDark ? 'border-amber-700' : 'border-amber-200',
          text: isDark ? 'text-amber-100' : 'text-amber-800',
          badge: 'bg-amber-600'
        }
      default:
        return {
          bg: isDark ? 'bg-gray-800' : 'bg-gray-50',
          border: isDark ? 'border-gray-700' : 'border-gray-200',
          text: isDark ? 'text-gray-300' : 'text-gray-700',
          badge: 'bg-gray-600'
        }
    }
  }

  const statusColor = getStatusColor(paper.status)

  return (
    <div className={`col-span-full sm:col-span-1 rounded-lg border p-4 transition-all hover:shadow-lg ${
      isDark
        ? `bg-gray-900 ${statusColor.border}`
        : `bg-white ${statusColor.border}`
    } border-gray-200 dark:border-gray-700`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3">
          <div className={`p-3 rounded-lg ${
            isDark ? 'bg-blue-950' : 'bg-blue-50'
          }`}>
            <FileText className={`w-5 h-5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
          </div>
          <div className="flex-1">
            <h3 className={`font-semibold mb-1 ${isDark ? 'text-gray-50' : 'text-gray-900'}`}>
              {paper.subject_code}
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Reg: {paper.register_number}
            </p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-semibold text-white ${statusColor.badge}`}>
          {paper.status}
        </span>
      </div>

      {/* File Info */}
      <div className={`text-xs mb-4 p-2 rounded ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
        <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
          <strong>File:</strong> {paper.filename}
        </p>
        <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
          <strong>Uploaded:</strong> {new Date(paper.uploaded_at).toLocaleDateString()}
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onView?.(paper)}
          className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-colors ${
            isDark
              ? 'bg-blue-950 text-blue-300 hover:bg-blue-900'
              : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
          }`}
        >
          <Eye className="w-4 h-4" />
          View
        </button>

        {paper.status?.toLowerCase() !== 'submitted' && (
          <button
            onClick={() => onSubmit?.(paper)}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-colors bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            <Upload className="w-4 h-4" />
            Submit
          </button>
        )}

        <button
          onClick={() => onReport?.(paper)}
          className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-colors ${
            isDark
              ? 'bg-orange-950 text-orange-300 hover:bg-orange-900'
              : 'bg-orange-50 text-orange-700 hover:bg-orange-100'
          }`}
        >
          <Flag className="w-4 h-4" />
          Report
        </button>
      </div>
    </div>
  )
}
