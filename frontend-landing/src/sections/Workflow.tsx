import { motion } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"

const workflowPhases = [
  {
    phase: "PHASE 1",
    title: "Administration & Setup",
    steps: [
      { num: "01", title: "Subject Mapping", desc: "Map subject codes to Moodle Assignment IDs (auto-discover from Moodle)" },
      { num: "02", title: "Student Mapping", desc: "Map register numbers to Moodle usernames" },
      { num: "03", title: "Scanning", desc: "Exam cell scans papers: {RegNo}_{SubCode}.pdf" }
    ]
  },
  {
    phase: "PHASE 2",
    title: "Staff Operations",
    steps: [
      { num: "01", title: "Login", desc: "Staff authenticates via JWT" },
      { num: "02", title: "Bulk Upload", desc: "Drag & drop scanned files with duplicate detection" },
      { num: "03", title: "Validation", desc: "Filename validation, SHA-256 hashing, mapping check" },
      { num: "04", title: "Smart Scan", desc: "Optional AI extraction via scanner agent + HF Spaces" },
      { num: "05", title: "Email", desc: "SendGrid notifies students of uploaded papers" }
    ]
  },
  {
    phase: "PHASE 3",
    title: "Student Operations",
    steps: [
      { num: "01", title: "Login", desc: "Moodle credentials authentication" },
      { num: "02", title: "Dashboard", desc: "View papers tagged with register number" },
      { num: "03", title: "Review", desc: "Secure PDF viewer to verify paper" },
      { num: "04", title: "Submit", desc: "One-click submission to Moodle LMS" },
      { num: "05", title: "Confirmation", desc: "Status updates to SUBMITTED_TO_LMS" }
    ]
  }
]

export function Workflow() {
  return (
    <section className="py-24 bg-[#f4f2ea] border-t-2 border-[#111111]" id="workflow">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeader 
          badge="How It Works." 
          title="Platform Workflow." 
          description="A streamlined 3-phase process ensuring secure and verified submissions."
        />

        <div className="max-w-5xl mx-auto mt-16 space-y-12">
          {workflowPhases.map((phase, phaseIdx) => (
            <motion.div
              key={phase.phase}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: phaseIdx * 0.1 }}
              className="flex flex-col md:flex-row gap-8"
            >
              <div className="md:w-1/3 shrink-0">
                <div className="sticky top-24">
                  <span className="font-mono text-xs font-bold tracking-widest text-[#2563eb] uppercase mb-2 block">
                    {phase.phase}
                  </span>
                  <h3 className="text-3xl font-serif text-[#111111] leading-tight pr-4">{phase.title}</h3>
                </div>
              </div>

              <div className="md:w-2/3">
                <div className="brutal-card p-0 overflow-hidden">
                  <div className="divide-y-2 divide-[#111111]">
                    {phase.steps.map((step) => (
                      <div 
                        key={step.num}
                        className="flex gap-6 p-6 bg-white hover:bg-[#f4f2ea] transition-colors"
                      >
                        <div className="font-mono text-lg font-bold text-[#a1a1aa] shrink-0 pt-0.5">
                          {step.num}
                        </div>
                        <div>
                          <h4 className="font-sans font-bold text-[#111111] mb-1">{step.title}</h4>
                          <p className="font-mono text-xs text-[#555555] leading-relaxed">{step.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* File naming box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-5xl mx-auto mt-24"
        >
          <div className="brutal-card p-10 text-center bg-white border-2 border-[#111111] border-dashed">
            <span className="font-mono text-xs font-bold tracking-widest text-[#555555] uppercase mb-6 block">File Naming Convention</span>
            
            <div className="flex flex-wrap justify-center items-center gap-2 text-2xl md:text-4xl font-mono font-bold mb-10 bg-[#f4f2ea] p-6 rounded border-2 border-[#111111] inline-flex shadow-[4px_4px_0px_#111111]">
              <span className="text-[#2563eb]">{`{RegNumber}`}</span>
              <span className="text-[#111111]">_</span>
              <span className="text-green-600">{`{SubCode}`}</span>
              <span className="text-[#111111]">.</span>
              <span className="text-[#555555]">{`{ext}`}</span>
            </div>

            <div className="flex flex-wrap justify-center gap-4">
              <span className="px-4 py-2 bg-white border-2 border-[#111111] font-mono text-sm text-[#111111]">
                <span className="text-[#2563eb]">611221104088</span>_<span className="text-green-600">19AI405</span>.pdf
              </span>
              <span className="px-4 py-2 bg-white border-2 border-[#111111] font-mono text-sm text-[#111111]">
                <span className="text-[#2563eb]">611221104089</span>_<span className="text-green-600">ML</span>.jpg
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
