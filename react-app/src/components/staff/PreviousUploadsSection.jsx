import React, { useState, useEffect } from 'react'
import { Search, RefreshCw, Eye, Flag, Trash2 } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import axios from 'axios'
import http from '../../api/api'

const getStatusBadge = (status) => {
  const statusMap = {
    pending: { bg: 'bg-yellow-100 dark:bg-yellow-950', text: 'text-yellow-900 dark:text-yellow-100', icon: '⏳' },
    processing: { bg: 'bg-blue-100 dark:bg-blue-950', text: 'text-blue-900 dark:text-blue-100', icon: '🔄' },
    submitted: { bg: 'bg-green-100 dark:bg-green-950', text: 'text-green-900 dark:text-green-100', icon: '✓' },
    failed: { bg: 'bg-red-100 dark:bg-red-950', text: 'text-red-900 dark:text-red-100', icon: '✗' },
    deleted: { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-900 dark:text-gray-100', icon: '🗑️' },
    completed: { bg: 'bg-green-100 dark:bg-green-950', text: 'text-green-900 dark:text-green-100', icon: '✓✓' },
  }

  const s = statusMap[status?.toLowerCase()] || { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-900 dark:text-gray-100', icon: '?' }
  return s
}

export const PreviousUploadsSection = ({ onRefresh }) => {
  const { authToken } = useAuth()
  const [files, setFiles] = useState([])
  const [filteredFiles, setFilteredFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  const loadFiles = async () => {
    setLoading(true)
    try {
      const endpoints = [
        '/upload/all',
        '/upload/list',
        '/upload/',
        '/artifacts',
      ]

      let response = null
      for (const endpoint of endpoints) {
        try {
          const res = await http().get(endpoint, {
            headers: { 'Authorization': `Bearer ${authToken}` },
          })
          if (res.status === 200) {
            response = res
            break
          }
        } catch (e) {
          // Try next endpoint
        }
      }

      if (!response) {
        setFiles([])
        setFilteredFiles([])
        return
      }

      let artifacts = response.data
      if (response.data.artifacts) artifacts = response.data.artifacts
      else if (response.data.files) artifacts = response.data.files
      else if (response.data.data) artifacts = response.data.data

      if (Array.isArray(artifacts)) {
        setFiles(artifacts)
        setFilteredFiles(artifacts)
      }
    } catch (error) {
      console.error('Error loading files:', error)
      setFiles([])
      setFilteredFiles([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFiles()
  }, [authToken])

  useEffect(() => {
    if (!searchQuery) {
      setFilteredFiles(files)
    } else {
      const q = searchQuery.toLowerCase()
      const filtered = files.filter((file) => {
        const filename = (file.filename || file.file_name || file.name || '').toLowerCase()
        const regNo = (file.register_number || file.reg_no || file.student_id || '').toLowerCase()
        const subject = (file.subject_code || file.sub_code || '').toLowerCase()
        const status = (file.status || '').toLowerCase()

        return (
          filename.includes(q) ||
          regNo.includes(q) ||
          subject.includes(q) ||
          status.includes(q)
        )
      })
      setFilteredFiles(filtered)
    }
  }, [searchQuery, files])

  return (
    <div className="bg-white dark:bg-gray-950 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden mt-6">
      {/* Header */}
      <div className="bg-primary-600 text-white px-6 py-4 flex justify-between items-center">
        <h3 className="text-lg font-bold font-poppins flex items-center gap-2 m-0">
          <Eye className="w-5 h-5" />
          Previously Uploaded Files
        </h3>
        <button
          onClick={() => {
            loadFiles()
            onRefresh?.()
          }}
          className="flex items-center gap-2 px-3 py-2 bg-white text-primary-600 rounded-lg hover:bg-gray-100 transition-colors text-sm font-semibold"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Body */}
      <div className="p-6">
        {/* Search Box */}
        <div className="mb-6 relative">
          <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input
            type="search"
            placeholder="Search files, reg no, subject, status..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
          />
        </div>

        {/* Content */}
        {loading ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <div className="animate-spin w-8 h-8 border-4 border-gray-200 dark:border-gray-700 border-t-primary-600 rounded-full mx-auto mb-3"></div>
            Loading...
          </div>
        ) : filteredFiles.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            {files.length === 0 ? 'No files uploaded yet' : 'No matching files'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left px-4 py-3 font-semibold text-gray-900 dark:text-gray-50">Filename</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-900 dark:text-gray-50">Reg No.</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-900 dark:text-gray-50">Subject</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-900 dark:text-gray-50">Status</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-900 dark:text-gray-50">Uploaded</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-900 dark:text-gray-50">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredFiles.map((file, index) => {
                  const statusStyle = getStatusBadge(file.status)
                  const uploadDate = file.uploaded_at || file.created_at || '-'

                  return (
                    <tr key={index} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900">
                      <td className="px-4 py-3 dark:text-gray-50">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">📄</span>
                          {file.filename || file.file_name || file.name || '-'}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded text-xs font-semibold">
                          {file.register_number || file.reg_no || file.student_id || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-primary-200 dark:bg-primary-900 text-primary-800 dark:text-primary-200 rounded text-xs font-semibold">
                          {file.subject_code || file.sub_code || file.subject || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${statusStyle.bg} ${statusStyle.text}`}>
                          {file.status || 'Unknown'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400 text-xs">
                        {uploadDate ? new Date(uploadDate).toLocaleString() : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button className="p-2 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded transition-colors" title="View Details">
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/30 rounded transition-colors" title="View Reports">
                            <Flag className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors" title="Delete">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
