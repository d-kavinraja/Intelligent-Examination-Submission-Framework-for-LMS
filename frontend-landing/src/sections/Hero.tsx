import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"

export function Hero() {
  return (
    <section className="relative min-h-[90vh] flex flex-col justify-center pt-32 pb-20 overflow-hidden" id="hero">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row items-center gap-16">
          
          {/* Left Column - Typography & CTA */}
          <div className="w-full lg:w-1/2">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-6xl md:text-7xl lg:text-8xl font-serif text-[#111111] leading-[0.95] tracking-tight mb-8"
            >
              Intelligent Examination <br />
              <span className="text-[#2563eb] italic pr-4">Submission</span> Framework.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-xl text-[#555555] mb-10 max-w-lg leading-relaxed"
            >
              An intelligent intermediary between the physical examination hall and the digital grading environment.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="flex flex-col items-start gap-4"
            >
              {/* Terminal mock command */}
              <div className="bg-[#111827] text-white px-4 py-3 rounded-md font-mono text-sm border-2 border-[#111111] shadow-[4px_4px_0px_#111111] w-full max-w-md flex justify-between items-center mb-4">
                <span className="truncate mr-4"><span className="text-[#2563eb]">$</span> git clone IESF-LMS.git</span>
                <button className="bg-white/10 hover:bg-white/20 px-2 py-1 rounded text-xs transition-colors shrink-0">copy</button>
              </div>

              <div className="flex flex-wrap gap-4">
                <a href="#installation" className="brutal-button flex items-center px-6 py-3 text-sm">
                  Get started <ArrowRight className="ml-2 h-4 w-4" />
                </a>
                <a href="https://github.com/d-kavinraja/Intelligent-Examination-Submission-Framework-for-LMS" target="_blank" rel="noreferrer" className="brutal-button-outline flex items-center px-6 py-3 text-sm bg-white">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="mr-2 h-4 w-4"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg> Star <span className="ml-2 px-2 py-0.5 rounded-full border border-[#111111] text-[10px]">IESF</span>
                </a>
              </div>
            </motion.div>
          </div>

          {/* Right Column - Dashboard Card */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="w-full lg:w-1/2 relative"
          >
            <div className="absolute -top-8 right-8 text-[#2563eb] font-serif italic text-xl z-10 pointer-events-none select-none">
              live from your server
            </div>
            
            <div className="hero-dash-card bg-[#f4f2ea] flex flex-col">
              <div className="p-4 border-b-2 border-[#111111] flex justify-between items-center bg-[#f4f2ea]">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="font-mono text-xs font-bold tracking-wider text-[#555555] uppercase">System Performance // Live</span>
                </div>
                <span className="font-mono text-xs font-bold tracking-wider text-[#555555] uppercase">CIA-1 & 2</span>
              </div>

              <div className="p-6 bg-white">
                <div className="hero-dash-header rounded flex justify-between items-end mb-6">
                  <div>
                    <div className="font-mono text-xs font-bold tracking-widest text-[#a1a1aa] mb-2 uppercase">API Endpoints / Core</div>
                    <div className="font-serif text-5xl">20+</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-xs text-green-400 mb-1">+100% vs manual</div>
                    {/* SVG mini chart placeholder */}
                    <svg width="60" height="20" viewBox="0 0 60 20" className="stroke-green-400 fill-none stroke-2 stroke-linecap-round stroke-linejoin-round">
                      <path d="M0 15 L10 10 L20 12 L30 5 L40 8 L50 2 L60 5" />
                    </svg>
                  </div>
                </div>

                <div className="space-y-4 mb-6">
                  <div className="flex justify-between items-center py-2 border-b border-dashed border-gray-300">
                    <span className="font-mono text-sm font-semibold">Audit Trail Coverage</span>
                    <span className="font-mono text-sm text-[#2563eb]">100%</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-dashed border-gray-300">
                    <span className="font-mono text-sm font-semibold">ML Extraction Accuracy</span>
                    <span className="font-mono text-sm text-[#2563eb]">&gt;95%</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-dashed border-gray-300">
                    <span className="font-mono text-sm font-semibold">Moodle Integration</span>
                    <span className="font-mono text-sm text-green-600 font-bold">Active</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-dashed border-gray-300">
                    <span className="font-mono text-sm font-semibold">Security Level</span>
                    <span className="font-mono text-sm text-[#2563eb]">AES-256</span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 pt-4 border-t-2 border-[#111111]">
                  <div className="text-center">
                    <div className="font-mono text-[10px] text-[#555555] uppercase tracking-wider mb-1">Process Rate</div>
                    <div className="font-serif text-2xl">Bulk</div>
                    <svg width="40" height="15" viewBox="0 0 40 15" className="stroke-green-500 fill-none stroke-2 mx-auto mt-1"><path d="M0 10 Q10 15 20 10 T40 5"/></svg>
                  </div>
                  <div className="text-center border-l-2 border-[#111111]">
                    <div className="font-mono text-[10px] text-[#555555] uppercase tracking-wider mb-1">Model</div>
                    <div className="font-serif text-2xl">YOLOv8</div>
                    <svg width="40" height="15" viewBox="0 0 40 15" className="stroke-[#2563eb] fill-none stroke-2 mx-auto mt-1"><path d="M0 10 L10 12 L20 8 L30 10 L40 5"/></svg>
                  </div>
                  <div className="text-center border-l-2 border-[#111111]">
                    <div className="font-mono text-[10px] text-[#555555] uppercase tracking-wider mb-1">Status</div>
                    <div className="font-serif text-2xl">Prod</div>
                    <svg width="40" height="15" viewBox="0 0 40 15" className="stroke-[#2563eb] fill-none stroke-2 mx-auto mt-1"><path d="M0 8 Q10 2 20 8 T40 8"/></svg>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
