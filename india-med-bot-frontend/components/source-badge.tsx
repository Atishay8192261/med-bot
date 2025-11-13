import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface SourceBadgeProps {
  source: string
  className?: string
}

const sourceConfig = {
  catalog: { label: "Catalog", variant: "secondary" as const },
  janaushadhi: { label: "Jan Aushadhi", variant: "default" as const },
  nppa: { label: "NPPA", variant: "outline" as const },
  dailymed: { label: "DailyMed", variant: "secondary" as const },
  openfda: { label: "OpenFDA", variant: "secondary" as const },
}

export function SourceBadge({ source, className }: SourceBadgeProps) {
  const config = sourceConfig[source as keyof typeof sourceConfig] || {
    label: source,
    variant: "outline" as const,
  }

  return (
    <Badge variant={config.variant} className={cn("text-xs", className)}>
      {config.label}
    </Badge>
  )
}
