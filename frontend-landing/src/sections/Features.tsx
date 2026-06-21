import { motion } from "framer-motion"

const integrations = [
  {
    name: "Moodle LMS",
    badges: ["SSO", "ASSIGNMENTS", "GRADES"],
    tag: "PROD"
  },
  {
    name: "FastAPI",
    badges: ["REST API", "JWT Auth", "ASYNC"],
    tag: "CORE"
  },
  {
    name: "PostgreSQL",
    badges: ["ACID", "JSONB", "BLOB"],
    tag: "DB"
  },
  {
    name: "HuggingFace",
    badges: ["YOLOv8", "CRNN", "INFERENCE"],
    tag: "ML"
  },
  {
    name: "SendGrid",
    badges: ["SMTP", "ALERTS", "TEMPLATES"],
    tag: "COMMS"
  }
]

export function Features() {
  return (
    <section className="py-24 bg-[#f4f2ea] border-t-2 border-[#111111]">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          
          {/* Left Column - Terminal (Dark Mode) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-[#111827] rounded-md border-2 border-[#111111] shadow-[8px_8px_0px_#111111] overflow-hidden"
          >
            <div className="flex items-center gap-2 px-4 py-3 border-b-2 border-[#111111] bg-[#1f2937]">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500 border border-[#111111]"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500 border border-[#111111]"></div>
                <div className="w-3 h-3 rounded-full bg-green-500 border border-[#111111]"></div>
              </div>
              <span className="font-mono text-[10px] text-white/50 tracking-widest ml-auto uppercase">~/IESF-LMS - TERMINAL</span>
            </div>
            
            <div className="p-6 font-mono text-sm leading-relaxed text-white/90">
              <div className="mb-2">
                <span className="text-[#2563eb]">$</span> <span className="font-bold">pip install -r requirements.txt</span>
              </div>
              <div className="text-white/60 mb-4">
                Collecting fastapi==0.95.1<br/>
                Downloading fastapi-0.95.1-py3-none-any.whl<br/>
                <span className="text-green-400 font-bold">Successfully installed dependencies</span>
              </div>
              
              <div className="mb-2">
                <span className="text-[#2563eb]">$</span> <span className="font-bold">python run.py</span>
              </div>
              <div className="text-[#2563eb] font-bold text-4xl leading-none my-4 tracking-tighter" style={{ textShadow: "2px 2px 0 #111" }}>
                IESF-LMS
              </div>
              <div className="space-y-1 mb-6">
                <div><span className="text-green-400">✓</span> Connected to postgres://localhost:5432</div>
                <div>User: <span className="text-white">admin@sec.ac.in</span></div>
                <div>Server: <span className="text-white">localhost:8000</span></div>
                <div><span className="text-green-400">✓</span> Moodle SSO ready. You're all set.</div>
              </div>
              <div className="flex items-center">
                <span className="text-[#2563eb] mr-2">$</span>
                <div className="w-2 h-4 bg-[#2563eb] animate-pulse"></div>
              </div>
            </div>
          </motion.div>

          {/* Right Column - Integration Cards */}
          <div>
            <div className="font-mono text-xs font-bold tracking-widest text-[#555555] uppercase mb-6">WORKS ACROSS YOUR STACK</div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {integrations.map((item, i) => (
                <motion.div
                  key={item.name}
                  initial={{ opacity: 0, x: 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="brutal-card-sm p-4 flex flex-col gap-4 hover:bg-[#f4f2ea] transition-colors cursor-default"
                >
                  <div className="flex justify-between items-start">
                    <span className="font-serif text-2xl text-[#111111]">{item.name}</span>
                    <span className="font-mono text-[10px] font-bold bg-[#2563eb] text-white px-1.5 py-0.5 rounded uppercase border border-[#111111]">
                      {item.tag}
                    </span>
                  </div>
                  
                  <div className="flex flex-wrap gap-1.5">
                    {item.badges.map(badge => (
                      <span key={badge} className="font-mono text-[9px] font-bold bg-[#111111] text-white px-1.5 py-0.5 rounded border border-[#111111] uppercase tracking-wider">
                        {badge}
                      </span>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
