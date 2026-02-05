import React, { useState, useRef } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useFileUpload } from '../../hooks/useFileUpload'
import axios from 'axios'
import { Navbar } from './Navbar'
import { StatsSection } from './StatsSection'
import { UploadZone } from './UploadZone'
import { FileList } from './FileList'
import { UploadSection } from './UploadSection'
import { UploadResults } from './UploadResults'
import { PreviousUploadsSection } from './PreviousUploadsSection'
import { LoadingOverlay } from '../LoadingOverlay'
import { Alert } from './Alert'
import http from '../../api/api'

export const UploadPortal = () => {
  const { authToken } = useAuth()
  const { selectedFiles, stats, addFiles, removeFile, clearFiles, getValidFiles, setUploadedCount } = useFileUpload()
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadResults, setUploadResults] = useState(null)
  const [showResults, setShowResults] = useState(false)
  const fileInputRef = useRef(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleUploadZone = ({ isDragOver: dragOver, files }) => {
    if (dragOver !== undefined) {
      setIsDragOver(dragOver)
    }
    if (files) {
      addFiles(files)
    }
  }

  const handleFileInputChange = (e) => {
    if (e.target.files) {
      addFiles(e.target.files)
    }
  }

  const handleUpload = async () => {
    const validFiles = getValidFiles()
    if (validFiles.length === 0) return

    setIsUploading(true)
    setUploadProgress(0)
    setShowResults(false)

    try {
      const formData = new FormData()
      validFiles.forEach(f => formData.append('files', f.file))
      formData.append('exam_session', new Date().toISOString().split('T')[0].replace(/-/g, ''))

      const response = await http().post('/upload/bulk', formData, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100)
          setUploadProgress(progress)
        }
      })

      if (response.status === 200) {
        setUploadResults({
          success: true,
          successful: response.data.successful || 0,
          total_files: response.data.total_files || validFiles.length,
          results: response.data.results || []
        })
        setUploadedCount((response.data.successful || 0))
        clearFiles()
        setRefreshKey(prev => prev + 1)
      }
    } catch (error) {
      console.error('Upload error:', error)
      setUploadResults({
        success: false,
        error: error.response?.data?.detail || error.message || 'Upload failed'
      })
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
      setShowResults(true)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <StatsSection stats={stats} />

        {/* Info Alert */}
        <Alert type="info" className="mb-6">
          <div>
            <strong>Filename Format:</strong> <code className="bg-gray-200 dark:bg-gray-700 dark:text-gray-50 px-2 py-1 rounded">{'{'} RegisterNumber {'}'}_{'{'} SubjectCode {'}'}. {'{'} pdf|jpg|jpeg|png {'}'}</code>
            <br />
            <small>Example: <code className="bg-gray-200 dark:bg-gray-700 dark:text-gray-50 px-2 py-1 rounded">611221104088_19AI405.pdf</code></small>
          </div>
        </Alert>

        {/* Upload Card */}
        <div className="bg-white dark:bg-gray-950 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden mb-6">
          <div className="bg-primary-600 text-white px-6 py-4">
            <h2 className="text-lg font-bold font-poppins m-0">Upload Examination Papers</h2>
          </div>

          <div className="p-6">
            {/* Upload Zone */}
            <UploadZone
              onDrop={handleUploadZone}
              onClick={() => fileInputRef.current?.click()}
              isDragOver={isDragOver}
            />
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileInputChange}
              className="hidden"
            />

            {/* File List */}
            {selectedFiles.length > 0 && (
              <FileList files={selectedFiles} onRemove={removeFile} />
            )}

            {/* Upload Section */}
            <UploadSection
              validFiles={getValidFiles()}
              stats={stats}
              onUpload={handleUpload}
              onClear={clearFiles}
              isUploading={isUploading}
              progress={uploadProgress}
            />
          </div>
        </div>

        {/* Upload Results */}
        <UploadResults results={uploadResults} show={showResults} />

        {/* Previous Uploads */}
        <PreviousUploadsSection key={refreshKey} onRefresh={() => {}} />
      </div>

      {/* Loading Overlay */}
      <LoadingOverlay show={isUploading} />
    </div>
  )
}
