import { ArrowUpRight } from "lucide-react"

export function Footer() {
  return (
    <footer className="border-t-2 border-[#111111] bg-[#f4f2ea] pt-16 pb-8">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="col-span-1 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <img src={`${import.meta.env.BASE_URL}logo.png`} alt="IESF-LMS Logo" className="h-8 w-auto object-contain" />
              <span className="font-serif text-3xl text-[#111111] tracking-tight">IESF-LMS</span>
            </div>
            <p className="font-mono text-xs text-[#555555] mb-6 leading-relaxed">
              An intelligent, AI-powered bridge for digitizing and submitting physical examination answer sheets to Moodle LMS.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-sans font-bold text-[#111111] mb-4">Product</h3>
            <ul className="space-y-3 font-mono text-sm">
              <li><a href="#features" className="text-[#555555] hover:text-[#2563eb] hover:underline underline-offset-4">Features</a></li>
              <li><a href="#architecture" className="text-[#555555] hover:text-[#2563eb] hover:underline underline-offset-4">Architecture</a></li>
              <li><a href="#workflow" className="text-[#555555] hover:text-[#2563eb] hover:underline underline-offset-4">Workflow</a></li>
              <li><a href="#api" className="text-[#555555] hover:text-[#2563eb] hover:underline underline-offset-4">API</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-sans font-bold text-[#111111] mb-4">Resources</h3>
            <ul className="space-y-3 font-mono text-sm">
              <li><a href="#installation" className="text-[#555555] hover:text-[#2563eb] hover:underline underline-offset-4">Setup Guide</a></li>
              <li><a href="https://exam-middleware.onrender.com/docs" target="_blank" rel="noreferrer" className="text-[#555555] hover:text-[#2563eb] hover:underline underline-offset-4 flex items-center gap-1">API Docs <ArrowUpRight className="h-3 w-3" /></a></li>
              <li><a href="https://kavinraja-ml-service.hf.space" target="_blank" rel="noreferrer" className="text-[#555555] hover:text-[#2563eb] hover:underline underline-offset-4 flex items-center gap-1">ML Service <ArrowUpRight className="h-3 w-3" /></a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-sans font-bold text-[#111111] mb-4">Legal</h3>
            <ul className="space-y-3 font-mono text-sm">
              <li><a href="#" className="text-[#555555] hover:text-[#111111]">Privacy Policy</a></li>
              <li><a href="#" className="text-[#555555] hover:text-[#111111]">Terms of Service</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t-2 border-[#111111] flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="font-mono text-xs text-[#555555]">
            &copy; {new Date().getFullYear()} D. Kavinraja, Santhan Kumar. Built for SEC.
          </p>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-green-500 border-2 border-[#111111]"></div>
            <span className="font-mono text-xs font-bold text-[#111111]">ALL SYSTEMS OPERATIONAL</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
