import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { useStudentAuth } from './contexts/StudentAuthContext'
import { useTheme } from './contexts/ThemeContext'
import { LoginSection } from './components/staff/LoginSection'
import { UploadPortal } from './components/staff/UploadPortal'
import { StudentLoginSection } from './components/student/StudentLoginSection'
import { StudentPortal } from './components/student/StudentPortal'
import { LoadingOverlay } from './components/LoadingOverlay'

function App() {
  const { authToken: staffToken, loading: staffLoading } = useAuth()
  const { authToken: studentToken } = useStudentAuth()
  const { isDark } = useTheme()

  React.useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  if (staffLoading) {
    return <LoadingOverlay show={true} />
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/staff" replace />} />
      <Route
        path="/staff"
        element={staffToken ? <UploadPortal /> : <LoginSection />}
      />
      <Route
        path="/student"
        element={studentToken ? <StudentPortal /> : <StudentLoginSection />}
      />
      <Route path="*" element={<Navigate to="/staff" replace />} />
    </Routes>
  )
}

export default App
