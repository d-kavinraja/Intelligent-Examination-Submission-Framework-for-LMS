import { motion } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"
import { Card } from "../components/ui/Card"

export function HumanInTheLoop() {
  const steps = [
    {
      number: "01",
      title: "Set boundaries",
      description: "Define policies and safety thresholds for your agents. Require approval for high-value transactions or sensitive API calls."
    },
    {
      number: "02",
      title: "Intercept & Review",
      description: "When an agent hits a boundary, it pauses execution and alerts your team via Slack or email for manual review."
    },
    {
      number: "03",
      title: "Approve or Correct",
      description: "Review the agent's planned actions, modify the prompt if necessary, and approve execution to resume the workflow."
    }
  ]

  return (
    <section id="hitl" className="py-20 md:py-32 relative">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeader
          sectionId="06"
          title="Keep humans in the loop."
          description="Never let autonomous agents run completely unchecked. Set guardrails and require manual approval for critical actions."
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
          {/* Connecting line for desktop */}
          <div className="hidden md:block absolute top-12 left-[10%] right-[10%] h-0.5 bg-border z-0">
            <motion.div 
              className="h-full bg-accent"
              initial={{ width: "0%" }}
              whileInView={{ width: "100%" }}
              viewport={{ once: true }}
              transition={{ duration: 1.5, ease: "easeInOut" }}
            />
          </div>

          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.3, duration: 0.5 }}
              className="relative z-10"
            >
              <Card className="p-8 h-full bg-[#0a0a0a] border-border/50 hover:border-accent/50 transition-colors">
                <div className="w-10 h-10 rounded-full bg-[#111] border border-border flex items-center justify-center text-sm font-mono text-accent mb-6">
                  {step.number}
                </div>
                <h3 className="text-xl font-bold text-foreground mb-3">{step.title}</h3>
                <p className="text-foreground/60 leading-relaxed">
                  {step.description}
                </p>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
