import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface PricePillProps {
  price: number
  label?: string
  className?: string
  variant?: "default" | "secondary" | "outline"
}

export function PricePill({ price, label, className, variant = "outline" }: PricePillProps) {
  return (
    <Badge variant={variant} className={cn("font-mono", className)}>
      {label && <span className="mr-1">{label}:</span>}₹{price.toFixed(2)}
    </Badge>
  )
}
