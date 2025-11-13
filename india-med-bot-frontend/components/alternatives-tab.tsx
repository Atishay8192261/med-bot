"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Eye, TrendingDown } from "lucide-react"
import { PricePill } from "@/components/price-pill"
import { SourceBadge } from "@/components/source-badge"
import { DisclaimerCard } from "@/components/disclaimer-card"
import { api } from "@/lib/api-client"
import type { AlternativesResponse } from "@/lib/types"
import { useRouter } from "next/navigation"

interface AlternativesTabProps {
  signature: string
}

export function AlternativesTab({ signature }: AlternativesTabProps) {
  const [alternatives, setAlternatives] = useState<AlternativesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    const loadAlternatives = async () => {
      try {
        setLoading(true)
        const data = await api.alternativesBySignature(signature)
        setAlternatives(data)
      } catch (err) {
        setError("Failed to load alternatives data")
        console.error("Error loading alternatives:", err)
      } finally {
        setLoading(false)
      }
    }

    loadAlternatives()
  }, [signature])

  const handleViewDrug = (drugSignature: string) => {
    if (drugSignature) {
      router.push(`/drug/${drugSignature}`)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <Card className="animate-pulse">
          <CardHeader>
            <div className="h-6 bg-muted rounded w-1/3"></div>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-8 bg-muted rounded w-16"></div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card className="animate-pulse">
          <CardContent className="p-0">
            <div className="h-64 bg-muted rounded"></div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !alternatives) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">{error || "No alternatives data available"}</p>
        </CardContent>
      </Card>
    )
  }

  const cheapestBrand = alternatives.brands.reduce(
    (min, brand) => (brand.mrp_inr && (!min.mrp_inr || brand.mrp_inr < min.mrp_inr) ? brand : min),
    alternatives.brands[0],
  )

  return (
    <div className="space-y-6">
      {/* Price Summary */}
      {alternatives.price_summary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5" />
              Price Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {alternatives.price_summary.min && (
                <PricePill price={alternatives.price_summary.min} label="Min" variant="outline" />
              )}
              {alternatives.price_summary.q1 && (
                <PricePill price={alternatives.price_summary.q1} label="Q1" variant="secondary" />
              )}
              {alternatives.price_summary.median && (
                <PricePill price={alternatives.price_summary.median} label="Median" variant="default" />
              )}
              {alternatives.price_summary.q3 && (
                <PricePill price={alternatives.price_summary.q3} label="Q3" variant="secondary" />
              )}
              {alternatives.price_summary.max && (
                <PricePill price={alternatives.price_summary.max} label="Max" variant="outline" />
              )}
            </div>
            {alternatives.price_summary.count && (
              <p className="text-sm text-muted-foreground mt-2">Based on {alternatives.price_summary.count} products</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Cheapest Options */}
      {cheapestBrand && (
        <Card>
          <CardHeader>
            <CardTitle className="text-primary">Cheapest Options</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-primary/5 rounded-lg">
              <div>
                <div className="font-semibold">{cheapestBrand.brand_name}</div>
                <div className="text-sm text-muted-foreground">{cheapestBrand.manufacturer}</div>
                {cheapestBrand.pack && <div className="text-xs text-muted-foreground">{cheapestBrand.pack}</div>}
              </div>
              <div className="text-right">
                {cheapestBrand.mrp_inr && (
                  <div className="text-2xl font-bold text-primary">₹{cheapestBrand.mrp_inr.toFixed(2)}</div>
                )}
                <div className="flex gap-1 mt-1">
                  {cheapestBrand.sources?.map((source, index) => (
                    <SourceBadge key={index} source={source} />
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Jan Aushadhi Highlight */}
      {alternatives.janaushadhi && alternatives.janaushadhi.length > 0 && (
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Badge variant="default" className="bg-primary">
                Jan Aushadhi
              </Badge>
              Generic Alternative Available
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alternatives.janaushadhi.map((drug, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-background rounded-lg">
                  <div>
                    <div className="font-medium">{drug.brand_name}</div>
                    <div className="text-sm text-muted-foreground">{drug.manufacturer}</div>
                  </div>
                  <div className="text-right">
                    {drug.mrp_inr && <div className="font-bold text-primary">₹{drug.mrp_inr.toFixed(2)}</div>}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* NPPA Ceiling Price */}
      {alternatives.nppa_ceiling_price && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">NPPA Ceiling Price</div>
                <div className="text-sm text-muted-foreground">
                  Maximum retail price set by National Pharmaceutical Pricing Authority
                </div>
              </div>
              <Badge variant="outline" className="text-lg font-bold">
                ₹{alternatives.nppa_ceiling_price.toFixed(2)}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alternatives Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Alternatives</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Brand</TableHead>
                <TableHead>Manufacturer</TableHead>
                <TableHead>Pack</TableHead>
                <TableHead>MRP (₹)</TableHead>
                <TableHead>Sources</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {alternatives.brands.map((brand, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{brand.brand_name}</TableCell>
                  <TableCell>{brand.manufacturer || "-"}</TableCell>
                  <TableCell>{brand.pack || "-"}</TableCell>
                  <TableCell>{brand.mrp_inr ? `₹${brand.mrp_inr.toFixed(2)}` : "-"}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {brand.sources?.map((source, sourceIndex) => (
                        <SourceBadge key={sourceIndex} source={source} />
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewDrug(brand.salt_signature || "")}
                      disabled={!brand.salt_signature}
                    >
                      <Eye className="h-3 w-3 mr-1" />
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <DisclaimerCard content={alternatives.disclaimer} />
    </div>
  )
}
