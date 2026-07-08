import { Routes, Route, Navigate } from 'react-router-dom'
import { Navbar } from "./components/layout/Navbar"
import { Footer } from "./components/layout/Footer"
import { Hero } from "./sections/Hero"
import { TheChallenge } from "./sections/TheChallenge"
import { Features } from "./sections/Features"
import { Architecture } from "./sections/Architecture"
import { Workflow } from "./sections/Workflow"
import { QuickStart } from "./sections/QuickStart"
import { APIEndpoints } from "./sections/APIEndpoints"
import StudentPortal from "./pages/StudentPortal"
import StudentLogin from "./pages/StudentLogin"

function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-[var(--color-brand-blue)]/30">
      <Navbar />
      <main className="flex-grow">
        <Hero />
        <TheChallenge />
        <Features />
        <Architecture />
        <Workflow />
        <APIEndpoints />
        <QuickStart />
      </main>
      <Footer />
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      {/* Redirect /portal to /portal/student */}
      <Route path="/portal" element={<Navigate to="/portal/student" replace />} />
      <Route path="/portal/student" element={<StudentPortal />} />
      <Route path="/portal/student/login" element={<StudentLogin />} />
    </Routes>
  )
}

export default App
