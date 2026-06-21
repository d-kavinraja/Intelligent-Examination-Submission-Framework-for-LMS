import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"

const accessPoints = [
  { title: "Staff Portal", url: "/portal/staff" },
  { title: "Student Portal", url: "/portal/student" },
  { title: "API Documentation", url: "/docs" },
  { title: "Health Check", url: "/health" },
  { title: "Production URL", url: "https://exam-middleware.onrender.com" },
  { title: "ML Service", url: "kavinraja-ml-service.hf.space" }
]

const endpoints = {
  auth: [
    { method: "POST", path: "/auth/staff/login", desc: "Staff login" },
    { method: "POST", path: "/auth/staff/register", desc: "Register staff (admin-only)" },
    { method: "POST", path: "/auth/student/login", desc: "Student login with Moodle creds" },
    { method: "POST", path: "/auth/student/logout", desc: "Student logout" }
  ],
  upload: [
    { method: "POST", path: "/upload/single", desc: "Upload single file" },
    { method: "POST", path: "/upload/bulk", desc: "Upload multiple files (with savepoints)" },
    { method: "POST", path: "/upload/validate", desc: "Validate filename format" },
    { method: "GET", path: "/upload/auto-processed", desc: "List auto-processed (ML) artifacts" },
    { method: "POST", path: "/upload/scan-upload", desc: "Smart Scan: AI process + upload" }
  ],
  student: [
    { method: "GET", path: "/student/dashboard", desc: "Get assigned papers & stats" },
    { method: "GET", path: "/student/paper/{id}/view", desc: "Secure PDF viewer" },
    { method: "POST", path: "/student/submit/{id}", desc: "Submit paper to Moodle" },
    { method: "GET", path: "/student/submission/{id}/status", desc: "Check submission status" }
  ],
  admin: [
    { method: "GET", path: "/admin/artifacts", desc: "List all artifacts (with filters)" },
    { method: "DELETE", path: "/admin/artifacts/{id}", desc: "Hard-delete artifact" },
    { method: "DELETE", path: "/admin/artifacts/purge-all", desc: "Purge all artifacts" },
    { method: "GET", path: "/admin/mappings", desc: "Subject mappings (CRUD)" },
    { method: "GET", path: "/admin/username-mappings", desc: "Student mappings (CRUD)" },
    { method: "POST", path: "/admin/attempt/{id}/lock", desc: "Lock/unlock attempt" },
    { method: "GET", path: "/admin/stats", desc: "System statistics" }
  ],
  extract: [
    { method: "POST", path: "/extract/process", desc: "Extract metadata from image via AI" },
    { method: "GET", path: "/extract/status", desc: "HF Spaces health check" }
  ]
}

const tabs = [
  { id: "auth", label: "Auth" },
  { id: "upload", label: "Upload" },
  { id: "student", label: "Student" },
  { id: "admin", label: "Admin" },
  { id: "extract", label: "Extract" }
]

export function APIEndpoints() {
  const [activeTab, setActiveTab] = useState("auth")

  const getMethodColor = (method: string) => {
    switch (method) {
      case "GET": return "bg-blue-100 text-blue-700 border-blue-200"
      case "POST": return "bg-green-100 text-green-700 border-green-200"
      case "DELETE": return "bg-red-100 text-red-700 border-red-200"
      default: return "bg-gray-100 text-gray-700 border-gray-200"
    }
  }

  return (
    <section className="py-24 bg-[#f4f2ea] border-t-2 border-[#111111]" id="api">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeader 
          badge="REST API" 
          title="Extensive endpoints." 
          description="Complete RESTful API with authentication, file management, extraction, and submission handling."
        />

        {/* Access Points Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-16 mt-16 max-w-5xl mx-auto">
          {accessPoints.map((ap, i) => (
            <motion.div
              key={ap.title}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
            >
              <div className="brutal-card-sm p-4 bg-white hover:shadow-[4px_4px_0px_#111111] transition-shadow cursor-default">
                <h4 className="font-sans font-bold text-[#111111] mb-2 text-sm">{ap.title}</h4>
                <code className="font-mono text-xs text-[#2563eb] bg-[#f4f2ea] px-2 py-1 rounded block truncate border border-[#111111]/10">
                  {ap.url}
                </code>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Endpoints Tabs */}
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 font-mono text-sm font-bold border-2 rounded transition-colors ${
                  activeTab === tab.id 
                    ? "bg-[#111111] text-white border-[#111111]" 
                    : "bg-white text-[#111111] border-[#111111] hover:bg-[#f4f2ea] shadow-[2px_2px_0px_#111111]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="brutal-card bg-white overflow-hidden min-h-[300px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="divide-y-2 divide-[#111111]"
              >
                {endpoints[activeTab as keyof typeof endpoints].map((ep, i) => (
                  <div key={i} className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-6 p-4 hover:bg-[#f4f2ea] transition-colors">
                    <div className={`font-mono text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded border-2 w-fit ${getMethodColor(ep.method)}`}>
                      {ep.method}
                    </div>
                    <code className="text-sm font-mono text-[#111111] flex-1 font-bold">
                      {ep.path}
                    </code>
                    <span className="font-mono text-xs text-[#555555] sm:w-1/3">
                      {ep.desc}
                    </span>
                  </div>
                ))}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  )
}
