import { motion } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"
import { Database, FileText, Server, Layers } from "lucide-react"

const schema = [
  { model: "ExaminationArtifact", desc: "Core entity — UUID, file path, SHA-256 hash, metadata, workflow status, exam_type, attempt, file_content (binary)" },
  { model: "SubjectMapping", desc: "Maps Subject Code → Moodle Assignment ID + Course ID with exam_type support" },
  { model: "UsernameRegMapping", desc: "Maps Moodle username → Register Number for student lookup" },
  { model: "StaffUser", desc: "Admin/staff accounts with bcrypt-hashed passwords and role flags" },
  { model: "StudentSession", desc: "Ephemeral sessions with AES-256 encrypted Moodle access tokens" },
  { model: "AuditLog", desc: "Immutable ledger of all actions with IP addresses and timestamps" },
  { model: "SubmissionQueue", desc: "Retry buffer for Moodle API failures — no submission is lost" }
]

export function Architecture() {
  return (
    <section className="py-24 bg-[#f4f2ea] border-t-2 border-[#111111]" id="architecture">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeader 
          badge="System Design" 
          title="Robust Architecture." 
          description="Designed for data integrity, security, and complete auditability across every step."
        />

        {/* 4-node flow using brutalist cards */}
        <div className="mt-16 mb-24 max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
            
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="z-10">
              <div className="brutal-card p-6 text-center h-full flex flex-col justify-center bg-white hover:bg-[#e5e3d9] transition-colors cursor-default">
                <div className="h-12 w-12 mx-auto border-2 border-[#111111] bg-[#f4f2ea] flex items-center justify-center mb-4 text-[#111111] shadow-[2px_2px_0px_#111111]">
                  <FileText className="h-6 w-6" />
                </div>
                <h4 className="font-sans font-bold text-[#111111] mb-1 text-sm">Physical Layer</h4>
                <p className="font-mono text-[10px] text-[#555555] mb-3">Scanned Answer Sheets</p>
                <span className="font-mono text-[10px] font-bold bg-[#111111] text-white px-2 py-1 rounded">PDF/JPG</span>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }} className="z-10">
              <div className="brutal-card p-6 text-center h-full flex flex-col justify-center bg-white hover:bg-[#e5e3d9] transition-colors cursor-default">
                <div className="h-12 w-12 mx-auto border-2 border-[#111111] bg-[#2563eb] flex items-center justify-center mb-4 text-white shadow-[2px_2px_0px_#111111]">
                  <Server className="h-6 w-6" />
                </div>
                <h4 className="font-sans font-bold text-[#111111] mb-1 text-sm">FastAPI Core</h4>
                <p className="font-mono text-[10px] text-[#555555] mb-3">PostgreSQL + JWT</p>
                <span className="font-mono text-[10px] font-bold bg-[#2563eb] text-white px-2 py-1 rounded">AUTH / API</span>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="z-10">
              <div className="brutal-card p-6 text-center h-full flex flex-col justify-center bg-white hover:bg-[#e5e3d9] transition-colors cursor-default">
                <div className="h-12 w-12 mx-auto border-2 border-[#111111] bg-green-500 flex items-center justify-center mb-4 text-[#111111] shadow-[2px_2px_0px_#111111]">
                  <Layers className="h-6 w-6" />
                </div>
                <h4 className="font-sans font-bold text-[#111111] mb-1 text-sm">HF Spaces</h4>
                <p className="font-mono text-[10px] text-[#555555] mb-3">YOLO + CRNN Models</p>
                <span className="font-mono text-[10px] font-bold bg-green-500 text-[#111111] px-2 py-1 rounded">INFERENCE</span>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.3 }} className="z-10">
              <div className="brutal-card p-6 text-center h-full flex flex-col justify-center bg-white hover:bg-[#e5e3d9] transition-colors cursor-default">
                <div className="h-12 w-12 mx-auto border-2 border-[#111111] bg-yellow-400 flex items-center justify-center mb-4 text-[#111111] shadow-[2px_2px_0px_#111111]">
                  <Database className="h-6 w-6" />
                </div>
                <h4 className="font-sans font-bold text-[#111111] mb-1 text-sm">Moodle LMS</h4>
                <p className="font-mono text-[10px] text-[#555555] mb-3">Assignment Submissions</p>
                <span className="font-mono text-[10px] font-bold bg-yellow-400 text-[#111111] px-2 py-1 rounded">SSO / SYNC</span>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Project Structure Tree */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-5xl mx-auto mb-16"
        >
          <div className="brutal-card bg-white p-6">
            <h3 className="font-sans font-bold text-[#111111] uppercase tracking-wide text-sm mb-4 border-b-2 border-[#111111] pb-2">Project Structure</h3>
            <pre className="font-mono text-sm text-[#555555] overflow-x-auto leading-relaxed">
<span className="text-[#111111] font-bold">IESF-LMS/</span>
├── <span className="text-[#2563eb] font-bold">exam_middleware/</span>      <span className="text-[#a1a1aa] italic"># Primary FastAPI middleware with database, services, and submission pipeline</span>
├── <span className="text-[#2563eb] font-bold">hf_space/</span>             <span className="text-[#a1a1aa] italic"># HuggingFace Space hosting YOLOv8 and CRNN models for text extraction</span>
├── <span className="text-[#2563eb] font-bold">moodle-docker/</span>        <span className="text-[#a1a1aa] italic"># Dockerized Moodle instance for testing and LMS integration</span>
├── <span className="text-[#2563eb] font-bold">frontend-landing/</span>     <span className="text-[#a1a1aa] italic"># React Landing Page (This application)</span>
├── <span className="text-green-600 font-bold">docker-compose.yml</span>    <span className="text-[#a1a1aa] italic"># Production deployment orchestration</span>
└── <span className="text-green-600 font-bold">index.html</span>            <span className="text-[#a1a1aa] italic"># Legacy Entry Point</span>
            </pre>
          </div>
        </motion.div>

        {/* Database Schema Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-5xl mx-auto"
        >
          <div className="brutal-card bg-white overflow-hidden">
            <div className="flex items-center gap-3 p-5 border-b-2 border-[#111111] bg-[#f4f2ea]">
              <Database className="h-5 w-5 text-[#2563eb]" />
              <h3 className="font-sans font-bold text-[#111111] uppercase tracking-wide text-sm">Database Schema</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b-2 border-[#111111] bg-white">
                    <th className="px-6 py-4 font-bold text-[#555555] uppercase w-1/3">Model</th>
                    <th className="px-6 py-4 font-bold text-[#555555] uppercase">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {schema.map((item, i) => (
                    <tr key={i} className="hover:bg-[#f4f2ea] transition-colors border-b border-dashed border-[#a1a1aa] last:border-0 group">
                      <td className="px-6 py-4">
                        <span className="text-[#2563eb] font-bold">
                          {item.model}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-[#555555] leading-relaxed group-hover:text-[#111111]">
                        {item.desc}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
