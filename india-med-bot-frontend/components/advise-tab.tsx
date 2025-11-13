"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, MessageSquare, ExternalLink } from "lucide-react"
import { DisclaimerCard } from "@/components/disclaimer-card"
import { SourceBadge } from "@/components/source-badge"
import { api } from "@/lib/api-client"
import type { AdviseResponse } from "@/lib/types"

interface AdviseTabProps {
  signature: string
  drugName: string
}

export function AdviseTab({ signature, drugName }: AdviseTabProps) {
  const [query, setQuery] = useState("")
  const [response, setResponse] = useState<AdviseResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)

    try {
      const result = await api.advise({
        signature,
        query: query.trim(),
        lang: "en",
      })
      setResponse(result)
    } catch (err) {
      setError("Failed to get advice. Please try again.")
      console.error("Error getting advice:", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Ask about {drugName}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Textarea
              placeholder={`Ask about this medicine... e.g., "What are the common side effects?" or "Can I take this with food?"`}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={3}
              className="resize-none"
            />
            <Button type="submit" disabled={loading || !query.trim()} className="w-full sm:w-auto">
              {loading ? (
                <>Loading...</>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Get Advice
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="border-destructive/20 bg-destructive/5">
          <CardContent className="p-4">
            <p className="text-destructive text-sm">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Response */}
      {response && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI Advice</CardTitle>
              {response.intent && <p className="text-sm text-muted-foreground">Intent: {response.intent}</p>}
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <div className="whitespace-pre-wrap text-sm leading-relaxed">{response.answer}</div>
              </div>
            </CardContent>
          </Card>

          {/* Sources */}
          {response.sources && response.sources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Sources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {response.sources.map((source, index) => (
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

          {/* Alternative Suggestions */}
          {response.alternatives && (
            <Card>
              <CardHeader>
                <CardTitle>Related Alternatives</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Based on your question, you might also be interested in these alternatives:
                </p>
                <div className="space-y-2">
                  {response.alternatives.brands.slice(0, 3).map((brand, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                      <div>
                        <div className="font-medium text-sm">{brand.brand_name}</div>
                        <div className="text-xs text-muted-foreground">{brand.manufacturer}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        {brand.mrp_inr && <span className="text-sm font-medium">₹{brand.mrp_inr.toFixed(2)}</span>}
                        <div className="flex gap-1">
                          {brand.sources?.map((source, sourceIndex) => (
                            <SourceBadge key={sourceIndex} source={source} />
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Disclaimer */}
          <DisclaimerCard content={response.disclaimer} />
        </div>
      )}

      {/* Default Disclaimer */}
      {!response && (
        <DisclaimerCard content="This AI advice is for informational purposes only and should not replace professional medical consultation. Always consult with healthcare professionals for medical decisions." />
      )}
    </div>
  )
}
