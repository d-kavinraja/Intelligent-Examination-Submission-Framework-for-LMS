import { motion } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"
import { Card } from "../components/ui/Card"
import { Badge } from "../components/ui/Badge"
import { Download, Star } from "lucide-react"

export function AgentRegistry() {
  const agents = [
    { name: "AutoGPT", author: "Significant-Gravitas", downloads: "1.2M", rating: "4.9", tags: ["Autonomous", "General"] },
    { name: "BabyAGI", author: "yoheinakajima", downloads: "850K", rating: "4.8", tags: ["Task Management"] },
    { name: "Devin", author: "Cognition", downloads: "420K", rating: "4.9", tags: ["Coding", "Software"] },
    { name: "ChatDev", author: "OpenBMB", downloads: "310K", rating: "4.7", tags: ["Software Team"] },
    { name: "MetaGPT", author: "geekan", downloads: "560K", rating: "4.8", tags: ["Multi-Agent"] },
    { name: "GPT-Researcher", author: "assafelovic", downloads: "280K", rating: "4.8", tags: ["Research"] },
  ]

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 }
    }
  }

  const item = {
    hidden: { opacity: 0, scale: 0.95 },
    show: { opacity: 1, scale: 1, transition: { duration: 0.4 } }
  }

  return (
    <section id="registry" className="py-20 md:py-32 relative bg-[#111111]/50 border-y border-border">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeader
          sectionId="02"
          title="Discover, share, and install agents."
          description="Access the largest registry of open-source and proprietary AI agents. Install them into your workspace with a single click."
        />

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {agents.map((agent, index) => (
            <motion.div key={index} variants={item}>
              <Card className="p-6 hover:bg-[#161616] cursor-pointer group">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-foreground text-lg group-hover:text-accent transition-colors">
                      {agent.name}
                    </h3>
                    <p className="text-sm text-foreground/50">{agent.author}</p>
                  </div>
                  <div className="flex items-center gap-1 text-yellow-500 text-sm font-medium">
                    <Star className="h-3.5 w-3.5 fill-current" />
                    <span>{agent.rating}</span>
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-2 mb-6">
                  {agent.tags.map(tag => (
                    <Badge key={tag} variant="outline" className="bg-background/50">{tag}</Badge>
                  ))}
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-border/50">
                  <div className="flex items-center gap-1.5 text-sm text-foreground/50">
                    <Download className="h-4 w-4" />
                    <span>{agent.downloads}</span>
                  </div>
                  <span className="text-sm font-medium text-accent opacity-0 group-hover:opacity-100 transition-opacity">
                    Install →
                  </span>
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
