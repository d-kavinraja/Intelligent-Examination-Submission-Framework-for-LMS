import { motion } from "framer-motion"

interface SectionHeaderProps {
  badge?: string
  sectionId?: string
  title: string
  description?: string
  align?: "left" | "center"
}

export function SectionHeader({ badge, sectionId, title, description, align = "left" }: SectionHeaderProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className={`mb-12 md:mb-16 ${align === "center" ? "text-center" : "text-left"}`}
    >
      <div className={`flex flex-col ${align === "center" ? "items-center" : "items-start"} gap-4`}>
        {badge && (
          <span className="font-mono text-[24px] italic text-[#2563eb]">
            {badge}
          </span>
        )}
        {sectionId && !badge && (
          <span className="font-mono text-sm font-bold tracking-widest text-[#555555] uppercase">
            {sectionId}
          </span>
        )}
        <h2 className="text-4xl md:text-6xl font-serif text-[#111111] max-w-3xl leading-[1.1]">
          {title}
        </h2>
        {description && (
          <p className="text-lg font-mono text-[#555555] max-w-2xl mt-2">
            {description}
          </p>
        )}
      </div>
    </motion.div>
  )
}
