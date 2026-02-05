import React from 'react'
import { CheckCircle2, AlertCircle, X } from 'lucide-react'

export const FileList = ({ files, onRemove }) => {
  return (
    <div className="mt-6 space-y-3">
      {files.map((file, index) => (
        <div
          key={index}
          className={`flex justify-between items-center p-5 rounded-xl border transition-all duration-200 ${
            file.valid
              ? 'bg-green-50 dark:bg-green-950 border-green-300 dark:border-green-700'
              : 'bg-red-50 dark:bg-red-950 border-red-300 dark:border-red-700'
          }`}
        >
          <div className="flex items-center gap-4 flex-1">
            {file.valid ? (
              <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
            )}

            <div className="flex-1">
              <div className="font-semibold text-gray-900 dark:text-gray-50">{file.name}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">{file.size}</div>
              {file.valid && (
                <div className="text-xs text-green-700 dark:text-green-300 font-semibold mt-1">
                  <span>✓ Reg: {file.registerNumber} | Subject: {file.subjectCode}</span>
                </div>
              )}
              {!file.valid && (
                <div className="text-xs text-red-700 dark:text-red-300 font-semibold mt-1">
                  {file.error}
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => onRemove(index)}
            className="p-2 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      ))}
    </div>
  )
}
