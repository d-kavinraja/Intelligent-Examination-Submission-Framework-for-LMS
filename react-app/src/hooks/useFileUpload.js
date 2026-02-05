import { useState, useCallback } from 'react'
import { validateFilename, formatFileSize } from '../utils/validation'

export const useFileUpload = () => {
  const [selectedFiles, setSelectedFiles] = useState([])
  const [stats, setStats] = useState({
    totalFiles: 0,
    validFiles: 0,
    invalidFiles: 0,
    uploadedFiles: 0
  })

  const addFiles = useCallback((files) => {
    const newFiles = Array.from(files).map((file) => {
      const validation = validateFilename(file.name)
      return {
        file,
        name: file.name,
        size: formatFileSize(file.size),
        valid: validation.valid,
        registerNumber: validation.registerNumber,
        subjectCode: validation.subjectCode,
        error: validation.error
      }
    })

    const updatedFiles = [...selectedFiles, ...newFiles]
    setSelectedFiles(updatedFiles)
    updateStats(updatedFiles)
  }, [selectedFiles])

  const removeFile = useCallback((index) => {
    const updatedFiles = selectedFiles.filter((_, i) => i !== index)
    setSelectedFiles(updatedFiles)
    updateStats(updatedFiles)
  }, [selectedFiles])

  const updateStats = (files) => {
    const total = files.length
    const valid = files.filter(f => f.valid).length
    const invalid = total - valid

    setStats({
      totalFiles: total,
      validFiles: valid,
      invalidFiles: invalid,
      uploadedFiles: stats.uploadedFiles
    })
  }

  const clearFiles = useCallback(() => {
    setSelectedFiles([])
    setStats({
      totalFiles: 0,
      validFiles: 0,
      invalidFiles: 0,
      uploadedFiles: 0
    })
  }, [])

  const getValidFiles = useCallback(() => {
    return selectedFiles.filter(f => f.valid)
  }, [selectedFiles])

  return {
    selectedFiles,
    stats,
    addFiles,
    removeFile,
    clearFiles,
    getValidFiles,
    setUploadedCount: (count) => {
      setStats(prev => ({ ...prev, uploadedFiles: count }))
    }
  }
}
