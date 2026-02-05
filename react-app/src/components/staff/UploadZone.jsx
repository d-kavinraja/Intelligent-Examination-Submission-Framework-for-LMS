import React from 'react'
import { CloudUpload } from 'lucide-react'

export const UploadZone = ({ onDrop, onClick, isDragOver }) => {
  const handleDragOver = (e) => {
    e.preventDefault()
    onDrop({ isDragOver: true })
  }

  const handleDragLeave = () => {
    onDrop({ isDragOver: false })
  }

  const handleDrop = (e) => {
    e.preventDefault()
    onDrop({ isDragOver: false, files: e.dataTransfer.files })
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={onClick}
      className={`border-2 border-dashed rounded-2xl p-14 text-center cursor-pointer transition-all duration-200 ${
        isDragOver
          ? 'border-primary-600 bg-blue-50 dark:bg-blue-950'
          : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 hover:border-primary-600 hover:bg-blue-50 dark:hover:bg-gray-800'
      }`}
    >
      <CloudUpload className="w-16 h-16 text-primary-600 mx-auto mb-4" />
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-50 font-poppins">Drag & Drop Files Here</h3>
      <p className="text-gray-600 dark:text-gray-400 mt-2">or click to browse your files</p>
    </div>
  )
}
