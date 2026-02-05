import React from 'react'
import { CheckCircle2, X } from 'lucide-react'

export const UploadResults = ({ results, show }) => {
  if (!show || !results) return null

  return (
    <div className="bg-white dark:bg-gray-950 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden mt-6">
      {/* Header */}
      <div className="bg-primary-600 text-white px-6 py-4">
        <h3 className="text-lg font-bold font-poppins flex items-center gap-2 m-0">
          <CheckCircle2 className="w-5 h-5" />
          Upload Results
        </h3>
      </div>

      {/* Body */}
      <div className="p-6">
        {results.success ? (
          <div className="mb-6 bg-green-50 dark:bg-green-950 border-l-4 border-green-600 dark:border-green-500 p-4 text-green-900 dark:text-green-50 text-sm">
            <span className="font-semibold">Successfully uploaded </span>
            <strong>{results.successful}</strong> of <strong>{results.total_files}</strong> files
          </div>
        ) : (
          <div className="mb-6 bg-red-50 dark:bg-red-950 border-l-4 border-red-600 dark:border-red-500 p-4 text-red-900 dark:text-red-50 text-sm">
            Upload failed: {results.error || 'Unknown error'}
          </div>
        )}

        {/* Results List */}
        {results.results && results.results.length > 0 && (
          <div className="space-y-2">
            {results.results.map((result, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900"
              >
                <div className="flex items-center gap-3 flex-1">
                  {result.success ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
                  ) : (
                    <X className="w-5 h-5 text-red-600 flex-shrink-0" />
                  )}
                  <span className="font-semibold text-gray-900 dark:text-gray-50">{result.filename}</span>
                </div>
                {result.success ? (
                  <span className="px-3 py-1.5 rounded-lg bg-green-600 text-white text-xs font-semibold">
                    Uploaded
                  </span>
                ) : (
                  <span className="px-3 py-1.5 rounded-lg bg-red-600 text-white text-xs font-semibold">
                    Failed: {result.error || 'Error'}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
