import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertTriangle } from "lucide-react"

interface DisclaimerCardProps {
  content: string
  className?: string
}

export function DisclaimerCard({ content, className }: DisclaimerCardProps) {
  return (
    <Alert className={className}>
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription className="text-sm">{content}</AlertDescription>
    </Alert>
  )
}
