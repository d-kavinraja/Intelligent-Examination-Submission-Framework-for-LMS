import React from 'react'
import { CloudUpload, Trash2 } from 'lucide-react'

export const UploadSection = ({ 
  validFiles, 
  stats,
  onUpload,
  onClear,
  isUploading,
  progress 
}) => {
  return (
    <div className="bg-white dark:bg-gray-950 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-primary-600 text-white px-6 py-4">
        <h2 className="text-lg font-bold font-poppins flex items-center gap-2 m-0">
          <CloudUpload className="w-5 h-5" />
          Upload Examination Papers
        </h2>
      </div>

      {/* Body */}
      <div className="p-6">
        {/* Progress Bar */}
        {isUploading && (
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <span className="font-semibold text-gray-900 dark:text-gray-50">Uploading files...</span>
              <span className="font-bold text-primary-600">Progress: {progress}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
              <div
                className="bg-primary-600 h-full transition-all duration-300 rounded-full"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onUpload}
            disabled={validFiles.length === 0 || isUploading}
            className="flex-1 px-4 py-3 rounded-lg bg-primary-600 text-white font-semibold flex items-center justify-center gap-2 hover:bg-primary-700 dark:hover:bg-primary-700 disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-all"
          >
            <CloudUpload className="w-5 h-5" />
            {isUploading ? 'Uploading...' : 'Upload Valid Files'}
          </button>
          <button
            onClick={onClear}
            className="px-4 py-3 rounded-lg border-2 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-primary-700 dark:hover:bg-primary-700 hover:text-white dark:hover:text-white hover:border-primary-700 dark:hover:border-primary-700 font-semibold flex items-center justify-center gap-2 transition-all"
          >
            <Trash2 className="w-5 h-5" />
            Clear All
          </button>
        </div>
      </div>
    </div>
  )
}
