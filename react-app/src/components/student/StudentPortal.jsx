import React, { useState, useEffect } from 'react'
import { useStudentAuth } from '../../contexts/StudentAuthContext'
import { useTheme } from '../../contexts/ThemeContext'
import axios from 'axios'
import { StudentNavbar } from './StudentNavbar'
import { StudentWelcomeBanner } from './StudentWelcomeBanner'
import { PaperCard } from './PaperCard'
import { LoadingOverlay } from '../LoadingOverlay'
import { AlertCircle, FileX } from 'lucide-react'

export const StudentPortal = () => {
  const { authToken, userInfo, logout } = useStudentAuth()
  const { isDark } = useTheme()
  const [papers, setPapers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState({ total: 0, pending: 0, submitted: 0 })
  const [pollInterval, setPollInterval] = useState(30000)
  const [reportCount, setReportCount] = useState(0)
  const [selectedPaper, setSelectedPaper] = useState(null)
  const [showViewModal, setShowViewModal] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)
  const [showSubmitModal, setShowSubmitModal] = useState(false)
  const [reportFormData, setReportFormData] = useState({
    message: '',
    suggestedReg: '',
    suggestedSub: '',
  })

  // Fetch papers
  const fetchPapers = async () => {
    try {
      const response = await axios.get('/api/student/papers', {
        headers: { 'Authorization': `Bearer ${authToken}` },
      })
      const papersList = response.data.papers || response.data || []
      setPapers(papersList)

      // Calculate stats
      const totalCount = papersList.length
      const pendingCount = papersList.filter(p => p.status?.toLowerCase() !== 'submitted').length
      const submittedCount = papersList.filter(p => p.status?.toLowerCase() === 'submitted').length

      setStats({
        total: totalCount,
        pending: pendingCount,
        submitted: submittedCount,
      })

      setError(null)
    } catch (err) {
      console.error('Error fetching papers:', err)
      setError('Failed to load papers. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPapers()
    const interval = setInterval(fetchPapers, pollInterval)
    return () => clearInterval(interval)
  }, [authToken, pollInterval])

  const handleViewPaper = (paper) => {
    setSelectedPaper(paper)
    setShowViewModal(true)
  }

  const handleSubmitPaper = (paper) => {
    setSelectedPaper(paper)
    setShowSubmitModal(true)
  }

  const handleReportPaper = (paper) => {
    setSelectedPaper(paper)
    setReportFormData({ message: '', suggestedReg: '', suggestedSub: '' })
    setShowReportModal(true)
  }

  const submitReport = async () => {
    try {
      await axios.post(
        `/api/student/papers/${selectedPaper.id}/report`,
        reportFormData,
        { headers: { 'Authorization': `Bearer ${authToken}` } }
      )
      setShowReportModal(false)
      setReportFormData({ message: '', suggestedReg: '', suggestedSub: '' })
    } catch (err) {
      console.error('Error submitting report:', err)
    }
  }

  const confirmSubmission = async () => {
    try {
      await axios.post(
        `/api/student/papers/${selectedPaper.id}/submit`,
        {},
        { headers: { 'Authorization': `Bearer ${authToken}` } }
      )
      setShowSubmitModal(false)
      fetchPapers()
    } catch (err) {
      console.error('Error submitting paper:', err)
      setError('Failed to submit paper. Please try again.')
    }
  }

  if (loading) {
    return <LoadingOverlay show={true} />
  }

  return (
    <div className={isDark ? 'bg-gray-950' : 'bg-gray-50'}>
      <StudentNavbar
        pollInterval={pollInterval}
        onPollIntervalChange={setPollInterval}
        reportCount={reportCount}
      />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Welcome Banner */}
        <StudentWelcomeBanner
          studentName={userInfo?.username || 'Student'}
          stats={stats}
        />

        {/* Error Alert */}
        {error && (
          <div className={`mb-6 p-4 rounded-lg flex gap-3 ${
            isDark ? 'bg-red-950 border border-red-700 text-red-50' : 'bg-red-50 border border-red-200 text-red-900'
          }`}>
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Papers Grid */}
        {papers.length === 0 ? (
          <div className={`rounded-lg p-8 text-center ${
            isDark ? 'bg-gray-900 border border-gray-800' : 'bg-white border border-gray-200'
          }`}>
            <FileX className={`w-12 h-12 mx-auto mb-3 ${
              isDark ? 'text-gray-600' : 'text-gray-400'
            }`} />
            <h3 className={`font-semibold mb-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              No Papers Available
            </h3>
            <p className={isDark ? 'text-gray-500' : 'text-gray-500'}>
              There are no examination papers assigned to your register number yet.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {papers.map((paper) => (
              <PaperCard
                key={paper.id}
                paper={paper}
                onView={handleViewPaper}
                onSubmit={handleSubmitPaper}
                onReport={handleReportPaper}
              />
            ))}
          </div>
        )}
      </div>

      {/* View Paper Modal */}
      {showViewModal && selectedPaper && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`rounded-lg max-w-2xl w-full max-h-[90vh] overflow-auto ${
            isDark ? 'bg-gray-900' : 'bg-white'
          }`}>
            <div className="sticky top-0 flex items-center justify-between p-4 border-b border-gray-700 dark:border-gray-800">
              <h3 className={`font-semibold ${isDark ? 'text-gray-50' : 'text-gray-900'}`}>
                {selectedPaper.subject_code}
              </h3>
              <button
                onClick={() => setShowViewModal(false)}
                className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
            <div className="p-4">
              <p className={`mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                <strong>File:</strong> {selectedPaper.filename}
              </p>
              <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-100'}`}>
                <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
                  Preview not available. Please download the file to view it.
                </p>
              </div>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-800 p-4 flex gap-2">
              <button
                onClick={() => setShowViewModal(false)}
                className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-colors ${
                  isDark
                    ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Close
              </button>
              {selectedPaper.status?.toLowerCase() !== 'submitted' && (
                <button
                  onClick={() => {
                    setShowViewModal(false)
                    handleSubmitPaper(selectedPaper)
                  }}
                  className="flex-1 px-4 py-2 rounded-lg font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
                >
                  Submit to Moodle
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Submit Modal */}
      {showSubmitModal && selectedPaper && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`rounded-lg max-w-md w-full ${isDark ? 'bg-gray-900' : 'bg-white'}`}>
            <div className="border-b border-gray-200 dark:border-gray-800 p-4">
              <h3 className={`font-semibold text-lg ${isDark ? 'text-gray-50' : 'text-gray-900'}`}>
                Confirm Submission
              </h3>
            </div>
            <div className="p-4">
              <p className={`mb-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                Are you sure you want to submit this paper to Moodle?
              </p>
              <div className={`p-3 rounded-lg mb-4 ${
                isDark ? 'bg-amber-950 border border-amber-700' : 'bg-amber-50 border border-amber-200'
              }`}>
                <p className={`text-sm ${isDark ? 'text-amber-100' : 'text-amber-900'}`}>
                  <strong>Important:</strong> This action will submit your answer sheet to Moodle. Please verify your paper before submitting.
                </p>
              </div>
              <div className={`p-3 rounded-lg mb-4 ${isDark ? 'bg-gray-800' : 'bg-gray-100'}`}>
                <p className={`text-sm mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <strong>Subject:</strong> <span className="text-emerald-600">{selectedPaper.subject_code}</span>
                </p>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <strong>File:</strong> {selectedPaper.filename}
                </p>
              </div>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-800 p-4 flex gap-2">
              <button
                onClick={() => setShowSubmitModal(false)}
                className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-colors ${
                  isDark
                    ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={confirmSubmission}
                className="flex-1 px-4 py-2 rounded-lg font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
              >
                Yes, Submit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Report Modal */}
      {showReportModal && selectedPaper && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`rounded-lg max-w-md w-full ${isDark ? 'bg-gray-900' : 'bg-white'}`}>
            <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-4 rounded-t-lg">
              <h3 className="font-semibold text-lg">Report an Issue</h3>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className={`block text-sm font-semibold mb-2 ${
                  isDark ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Describe the problem
                </label>
                <textarea
                  value={reportFormData.message}
                  onChange={(e) => setReportFormData(prev => ({...prev, message: e.target.value}))}
                  placeholder="Explain what's wrong..."
                  rows="4"
                  className={`w-full px-3 py-2 rounded-lg border transition-colors ${
                    isDark
                      ? 'bg-gray-800 border-gray-700 text-gray-50 placeholder-gray-500 focus:border-orange-500'
                      : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500 focus:border-orange-500'
                  }`}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={`block text-sm font-semibold mb-2 ${
                    isDark ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    Suggested Reg No
                  </label>
                  <input
                    type="text"
                    value={reportFormData.suggestedReg}
                    onChange={(e) => setReportFormData(prev => ({...prev, suggestedReg: e.target.value}))}
                    placeholder="12-digit (optional)"
                    maxLength="12"
                    className={`w-full px-3 py-2 rounded-lg border transition-colors text-sm ${
                      isDark
                        ? 'bg-gray-800 border-gray-700 text-gray-50 placeholder-gray-500 focus:border-orange-500'
                        : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500 focus:border-orange-500'
                    }`}
                  />
                </div>
                <div>
                  <label className={`block text-sm font-semibold mb-2 ${
                    isDark ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    Suggested Subject
                  </label>
                  <input
                    type="text"
                    value={reportFormData.suggestedSub}
                    onChange={(e) => setReportFormData(prev => ({...prev, suggestedSub: e.target.value}))}
                    placeholder="e.g. 19AI405"
                    className={`w-full px-3 py-2 rounded-lg border transition-colors text-sm ${
                      isDark
                        ? 'bg-gray-800 border-gray-700 text-gray-50 placeholder-gray-500 focus:border-orange-500'
                        : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500 focus:border-orange-500'
                    }`}
                  />
                </div>
              </div>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-800 p-4 flex gap-2">
              <button
                onClick={() => setShowReportModal(false)}
                className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-colors ${
                  isDark
                    ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={submitReport}
                className="flex-1 px-4 py-2 rounded-lg font-semibold bg-red-600 hover:bg-red-700 text-white transition-colors"
              >
                Submit Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
