import { motion } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"
import { Card } from "../components/ui/Card"
import { Sparkles, AlertTriangle, ArrowUpRight } from "lucide-react"

export function AgentInsights() {
  const insights = [
    {
      type: "optimization",
      icon: <Sparkles className="h-5 w-5 text-accent" />,
      title: "Prompt Optimization",
      description: "AutoGPT is using 40% more tokens than necessary in its context window. Compressing the system prompt could save ~$42/day.",
      action: "Review suggested prompt"
    },
    {
      type: "warning",
      icon: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
      title: "High Latency Detected",
      description: "CustomerBot API calls to us-east-1 are experiencing 2.4s average latency over the last hour. Consider routing to us-west-2.",
      action: "View network trace"
    }
  ]

  return (
    <section id="insights" className="py-20 md:py-32 relative bg-[#111111]/50 border-y border-border">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-24 items-center">
          <div>
            <SectionHeader
              sectionId="04"
              title="Insights that save you time and money."
              description="Our AI continuously analyzes your agent's behavior to find performance bottlenecks, security risks, and cost optimizations automatically."
            />
            
            <div className="space-y-4">
              {['Automated cost optimization', 'Latency anomaly detection', 'Prompt injection blocking'].map((feature, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent/20 text-accent">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-foreground/80">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            {insights.map((insight, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.2, duration: 0.5 }}
              >
                <Card className="p-6 relative overflow-hidden group">
                  <div className={`absolute top-0 left-0 w-1 h-full ${insight.type === 'optimization' ? 'bg-accent' : 'bg-yellow-500'}`} />
                  <div className="flex gap-4">
                    <div className="mt-1 flex-shrink-0">
                      {insight.icon}
                    </div>
                    <div>
                      <h4 className="font-bold text-foreground mb-1">{insight.title}</h4>
                      <p className="text-foreground/60 text-sm mb-4 leading-relaxed">
                        {insight.description}
                      </p>
                      <button className="text-sm font-medium text-foreground hover:text-accent transition-colors flex items-center gap-1 group-hover:gap-2">
                        {insight.action} <ArrowUpRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
