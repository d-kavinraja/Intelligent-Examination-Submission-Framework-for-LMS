import React from "react"
import { cn } from "../../lib/utils"

export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-xl border border-border bg-[#111111] text-foreground shadow-sm transition-all hover:border-border/80",
        className
      )}
      {...props}
    />
  )
)
Card.displayName = "Card"
