import { useState } from "react"
import { Check, Copy } from "lucide-react"

export function Terminal({ command, title, icon }: { command: string, title?: string, icon?: React.ReactNode }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(command)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="rounded-xl border border-white/10 bg-[#050505] overflow-hidden shadow-2xl">
      {(title || icon) && (
        <div className="flex items-center justify-between px-4 py-3 bg-white/[0.02] border-b border-white/5">
          <div className="flex items-center gap-2">
            {icon}
            <span className="text-xs font-mono text-muted-foreground">{title}</span>
          </div>
        </div>
      )}
      <div className="relative flex items-start justify-between px-4 py-4 font-mono text-sm text-foreground/80">
        <div className="flex flex-col gap-2 overflow-x-auto whitespace-pre scrollbar-hide flex-1 pt-1">
          {command.split('\n').map((line, i) => (
            <div key={i} className="flex gap-4">
              <span className="text-muted-foreground/30 select-none shrink-0 w-4 text-right">{i + 1}</span>
              <span className={line.startsWith('#') ? 'text-muted-foreground' : 'text-foreground/90'}>
                {line}
              </span>
            </div>
          ))}
        </div>
        <button
          onClick={handleCopy}
          className="ml-4 rounded-md p-1.5 text-foreground/50 hover:bg-white/10 hover:text-foreground transition-colors shrink-0"
          aria-label="Copy to clipboard"
        >
          {copied ? <Check className="h-4 w-4 text-[var(--color-brand-green)]" /> : <Copy className="h-4 w-4" />}
        </button>
      </div>
    </div>
  )
}
