import { motion } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"
import { Card } from "../components/ui/Card"
import { Badge } from "../components/ui/Badge"
import { Activity, Clock, Server } from "lucide-react"

export function Observability() {
  const traces = [
    { id: "tr_8f92a1b", agent: "AutoGPT", status: "success", duration: "1.2s", model: "gpt-4-turbo", cost: "$0.012" },
    { id: "tr_7e54c2d", agent: "DataAnalyzer", status: "running", duration: "4.5s", model: "claude-3-opus", cost: "~$0.045" },
    { id: "tr_3b19f4e", agent: "CustomerBot", status: "error", duration: "0.8s", model: "gpt-3.5-turbo", cost: "$0.001" },
    { id: "tr_9a22d5c", agent: "CodeReviewer", status: "success", duration: "2.4s", model: "gpt-4-turbo", cost: "$0.028" },
    { id: "tr_4c66e1f", agent: "AutoGPT", status: "success", duration: "1.8s", model: "gpt-4-turbo", cost: "$0.018" },
  ]

  return (
    <section id="observability" className="py-20 md:py-32 relative">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeader
          sectionId="03"
          title="See inside the black box."
          description="Real-time observability for your agents. Trace every execution, monitor costs, and debug failures instantly."
        />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <Card className="overflow-hidden border-border/50 bg-[#0a0a0a]">
            {/* Table Header / Toolbar */}
            <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-b border-border/50 gap-4 bg-[#111]">
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1.5 text-foreground/70">
                  <Activity className="h-4 w-4" />
                  <span>Live Stream</span>
                </div>
                <div className="h-4 w-px bg-border"></div>
                <div className="flex items-center gap-1.5 text-foreground/70">
                  <Server className="h-4 w-4" />
                  <span>US-East</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-accent"></span>
                </span>
                <span className="text-sm font-medium text-accent">Listening for traces...</span>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-[#161616] text-foreground/50 border-b border-border/50">
                  <tr>
                    <th className="px-6 py-3 font-medium">Trace ID</th>
                    <th className="px-6 py-3 font-medium">Agent</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                    <th className="px-6 py-3 font-medium">Model</th>
                    <th className="px-6 py-3 font-medium">Duration</th>
                    <th className="px-6 py-3 font-medium text-right">Cost</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/20">
                  {traces.map((trace, i) => (
                    <motion.tr 
                      key={trace.id}
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 0.1, duration: 0.3 }}
                      className="hover:bg-[#161616]/50 transition-colors cursor-pointer"
                    >
                      <td className="px-6 py-4 font-mono text-foreground/70">{trace.id}</td>
                      <td className="px-6 py-4 font-medium text-foreground">{trace.agent}</td>
                      <td className="px-6 py-4">
                        <Badge 
                          variant={trace.status === 'success' ? 'success' : trace.status === 'running' ? 'outline' : 'default'}
                          className={trace.status === 'error' ? 'bg-red-500/20 text-red-500 border-transparent' : trace.status === 'running' ? 'border-accent/50 text-accent animate-pulse' : ''}
                        >
                          {trace.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-foreground/60">{trace.model}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-foreground/60">
                          <Clock className="h-3.5 w-3.5" />
                          {trace.duration}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right font-mono text-foreground/70">{trace.cost}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      </div>
    </section>
  )
}
