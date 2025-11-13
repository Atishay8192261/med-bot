"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Button } from "@/components/ui/button"
import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react"
import { DisclaimerCard } from "@/components/disclaimer-card"
import { api } from "@/lib/api-client"
import type { MonographResponse } from "@/lib/types"

interface MonographTabProps {
  signature: string
}

export function MonographTab({ signature }: MonographTabProps) {
  const [monograph, setMonograph] = useState<MonographResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    uses: true,
    how_to_take: false,
    precautions: false,
    side_effects: false,
  })

  useEffect(() => {
    const loadMonograph = async () => {
      try {
        setLoading(true)
        const data = await api.monographBySignature(signature)
        setMonograph(data)
      } catch (err) {
        setError("Failed to load monograph data")
        console.error("Error loading monograph:", err)
      } finally {
        setLoading(false)
      }
    }

    loadMonograph()
  }, [signature])

  const toggleSection = (section: string) => {
    setOpenSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  const sectionTitles = {
    uses: "Uses",
    how_to_take: "How to take",
    precautions: "Precautions",
    side_effects: "Side effects",
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-6 bg-muted rounded w-1/3"></div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="h-4 bg-muted rounded w-full"></div>
                <div className="h-4 bg-muted rounded w-3/4"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error || !monograph) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">{error || "No monograph data available"}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Monograph Sections */}
      <div className="space-y-4">
        {Object.entries(sectionTitles).map(([key, title]) => {
          const content = monograph.sections[key as keyof typeof monograph.sections]
          const isOpen = openSections[key]

          return (
            <Card key={key}>
              <Collapsible open={isOpen} onOpenChange={() => toggleSection(key)}>
                <CollapsibleTrigger asChild>
                  <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-3">
                        {title}
                        {!content && <span className="text-sm font-normal text-muted-foreground">(Not available)</span>}
                      </CardTitle>
                      <Button variant="ghost" size="sm" className="p-0 h-auto">
                        {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </Button>
                    </div>
                  </CardHeader>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <CardContent>
                    {content && content.length > 0 ? (
                      <ul className="space-y-2">
                        {content.map((item, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <span className="text-primary mt-1.5 text-xs">•</span>
                            <span className="text-sm leading-relaxed">{item}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">
                        Information not available yet. Our system is continuously updated with new data from trusted
                        medical sources.
                      </p>
                    )}
                  </CardContent>
                </CollapsibleContent>
              </Collapsible>
            </Card>
          )
        })}
      </div>

      {/* Sources */}
      {monograph.sources && monograph.sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {monograph.sources.map((source, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                  <div>
                    <div className="font-medium text-sm">{source.name}</div>
                    <div className="text-xs text-muted-foreground">{source.url}</div>
                  </div>
                  <Button variant="outline" size="sm" asChild>
                    <a href={source.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      <DisclaimerCard content={monograph.disclaimer} />
    </div>
  )
}
