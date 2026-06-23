import { motion } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"

export function TheChallenge() {
  return (
    <section className="py-24 bg-[#f4f2ea] border-t-2 border-[#111111]" id="features">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-end mb-12">
          <SectionHeader 
            badge="Stay secure." 
            title="Complete transparency." 
          />
          <div className="hidden md:block font-mono text-sm text-right text-[#555555] max-w-xs">
            Build systems for complex or sensitive tasks requiring human oversight.
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Large Card - Workflow Sessions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="lg:col-span-7 brutal-card p-6 flex flex-col"
          >
            <div className="flex justify-between items-center mb-6">
              <span className="font-mono text-xs font-bold tracking-widest text-[#555555] uppercase">01 WORKFLOW SESSIONS</span>
              <span className="brutal-badge text-white bg-[#2563eb]">LIVE</span>
            </div>
            <h3 className="text-3xl font-serif text-[#111111] mb-8">Real-time artifact ingestion</h3>

            <div className="w-full border-2 border-[#111111] rounded bg-white overflow-hidden">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b-2 border-[#111111] bg-[#f4f2ea]">
                    <th className="px-4 py-3 font-bold text-[#555555] uppercase">AGENT / PROCESS</th>
                    <th className="px-4 py-3 font-bold text-[#555555] uppercase">TASK</th>
                    <th className="px-4 py-3 font-bold text-[#555555] uppercase">DURATION</th>
                    <th className="px-4 py-3 font-bold text-[#555555] uppercase">STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-dashed border-[#555555]">
                    <td className="px-4 py-4 text-[#2563eb]">bulk_upload_job</td>
                    <td className="px-4 py-4">Process CIA-1 Bundle</td>
                    <td className="px-4 py-4">2m 14s</td>
                    <td className="px-4 py-4 text-green-600 font-bold flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-green-500"></div> done</td>
                  </tr>
                  <tr className="border-b border-dashed border-[#555555]">
                    <td className="px-4 py-4 text-[#2563eb]">artifact_validator</td>
                    <td className="px-4 py-4">Validate SHA-256 hash & mapping</td>
                    <td className="px-4 py-4">0m 12s</td>
                    <td className="px-4 py-4 text-green-600 font-bold flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-green-500"></div> done</td>
                  </tr>
                  <tr className="border-b border-dashed border-[#555555]">
                    <td className="px-4 py-4 text-[#2563eb]">yolo_crnn_worker</td>
                    <td className="px-4 py-4">Extract 611221104088_19AI405</td>
                    <td className="px-4 py-4">1m 48s</td>
                    <td className="px-4 py-4 text-green-600 font-bold flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-green-500"></div> done</td>
                  </tr>
                  <tr className="border-b border-dashed border-[#555555]">
                    <td className="px-4 py-4 text-[#2563eb]">moodle_sync</td>
                    <td className="px-4 py-4">Submit Assignment ID 24</td>
                    <td className="px-4 py-4">3m 02s</td>
                    <td className="px-4 py-4 text-green-600 font-bold flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-green-500"></div> done</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-4 text-[#2563eb]">email_notifier</td>
                    <td className="px-4 py-4">SendGrid dispatch student</td>
                    <td className="px-4 py-4">0m 58s</td>
                    <td className="px-4 py-4 text-[#2563eb] font-bold flex items-center gap-2"><div className="w-2 h-2 rounded-full border-2 border-[#2563eb] border-t-transparent animate-spin"></div> running</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="mt-6 flex gap-6 font-mono text-sm font-bold text-[#111111]">
              <span>4 completed</span>
              <span className="text-[#2563eb]">1 in progress</span>
              <span className="text-green-600 ml-auto">avg accuracy: 98.5%</span>
            </div>
          </motion.div>

          {/* Right Column */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            
            {/* Top Right - Upload Batch Stats */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="brutal-card p-6 flex flex-col h-1/2"
            >
              <div className="font-mono text-xs font-bold tracking-widest text-[#555555] mb-2 uppercase">02 INGESTION TRACKER</div>
              <h3 className="text-3xl font-serif text-[#111111] mb-6">Upload batch visibility</h3>
              
              <div className="flex items-end gap-2 h-24 mb-4 mt-auto">
                {/* Bar chart mock */}
                {[4, 6, 3, 7, 5, 8, 4, 9, 3, 6, 8, 5].map((h, i) => (
                  <div key={i} className={`flex-1 ${i % 3 === 0 ? 'bg-[#2563eb]' : 'bg-[#93c5fd]'} rounded-t-sm`} style={{ height: `${h * 10}%` }}></div>
                ))}
              </div>
              
              <div className="flex justify-between items-center border-t-2 border-[#111111] pt-2">
                <span className="font-mono text-[10px] font-bold text-[#555555] uppercase">14 DAYS AGO</span>
                <span className="font-mono text-[10px] font-bold text-[#555555] uppercase">TODAY</span>
              </div>
            </motion.div>

            {/* Bottom Right - Model Insights */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="brutal-card p-6 flex flex-col h-1/2"
            >
              <div className="font-mono text-xs font-bold tracking-widest text-[#555555] mb-2 uppercase">03 MODEL INSIGHTS</div>
              <h3 className="text-3xl font-serif text-[#111111] mb-6">Strategize AI inference</h3>
              
              <div className="space-y-6 mt-auto">
                <div>
                  <div className="flex justify-between font-mono text-xs font-bold mb-2">
                    <span>YOLOv8 Detection</span>
                    <span>124ms</span>
                  </div>
                  <div className="h-2 w-full bg-[#f4f2ea] border border-[#111111] rounded-full overflow-hidden">
                    <div className="h-full bg-[#2563eb] w-[85%]"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between font-mono text-xs font-bold mb-2">
                    <span>CRNN Text Recog</span>
                    <span>89ms</span>
                  </div>
                  <div className="h-2 w-full bg-[#f4f2ea] border border-[#111111] rounded-full overflow-hidden">
                    <div className="h-full bg-green-500 w-[60%]"></div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  )
}
