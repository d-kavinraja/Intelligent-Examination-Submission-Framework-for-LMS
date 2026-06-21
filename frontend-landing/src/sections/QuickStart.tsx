import { ArrowRight, Check } from "lucide-react"

export function QuickStart() {
  return (
    <section className="bg-dark-section py-32 border-y-2 border-[#111111]" id="installation">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-16 items-start">
          
          {/* Left Column */}
          <div className="w-full md:w-1/2">
            <span className="font-mono text-xs font-bold tracking-widest text-[#a1a1aa] uppercase mb-6 block">DEPLOY YOUR WAY</span>
            
            <h2 className="text-5xl md:text-7xl font-serif text-white leading-[1.1] mb-8">
              Cloud deployed or <br/>
              <span className="text-[#2563eb] italic">self-hosted.</span> Your call.
            </h2>
            
            <p className="font-mono text-sm text-[#d4d4d8] mb-10 max-w-md leading-relaxed">
              We offer fully containerized solutions with SSO, dedicated infrastructure, and PostgreSQL. Or self-host on your own infra with Docker Compose. Same product, your choice.
            </p>
            
            <div className="flex flex-wrap gap-4">
              <a href="https://exam-middleware.onrender.com" target="_blank" rel="noreferrer" className="bg-[#2563eb] text-white border-2 border-[#2563eb] hover:bg-[#1d4ed8] px-6 py-3 font-mono font-bold text-sm rounded flex items-center transition-colors">
                Live Demo <ArrowRight className="ml-2 h-4 w-4" />
              </a>
              <a href="https://github.com/d-kavinraja/Intelligent-Examination-Submission-Framework-for-LMS" target="_blank" rel="noreferrer" className="bg-transparent text-white border-2 border-white hover:bg-white/10 px-6 py-3 font-mono font-bold text-sm rounded flex items-center transition-colors">
                Read docs <ArrowRight className="ml-2 h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Right Column */}
          <div className="w-full md:w-1/2 pt-10 md:pt-16">
            <div className="space-y-8">
              
              <div className="flex gap-4">
                <Check className="h-5 w-5 text-[#2563eb] shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-sans font-bold text-white mb-1">Managed Cloud (Render)</h4>
                  <p className="font-mono text-xs text-[#a1a1aa] leading-relaxed">
                    We deploy, scale, and maintain the FastAPI service. You just use it.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <Check className="h-5 w-5 text-[#2563eb] shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-sans font-bold text-white mb-1">Self-Host</h4>
                  <p className="font-mono text-xs text-[#a1a1aa] leading-relaxed">
                    Docker Compose up. Postgres + ML Worker + Redis. Your data stays yours.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <Check className="h-5 w-5 text-[#2563eb] shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-sans font-bold text-white mb-1">Moodle SSO</h4>
                  <p className="font-mono text-xs text-[#a1a1aa] leading-relaxed">
                    Enterprise authentication natively integrating with your existing LMS identity provider.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <Check className="h-5 w-5 text-[#2563eb] shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-sans font-bold text-white mb-1">HuggingFace Spaces</h4>
                  <p className="font-mono text-xs text-[#a1a1aa] leading-relaxed">
                    Dedicated ML infrastructure for YOLOv8 and CRNN text extraction.
                  </p>
                </div>
              </div>

            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
