"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { GlobalSearchBar } from "@/components/global-search-bar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Pill, Home, ChevronRight, Languages, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { MonographTab } from "@/components/monograph-tab"
import { AlternativesTab } from "@/components/alternatives-tab"
import { AdviseTab } from "@/components/advise-tab"
import { api } from "@/lib/api-client"
import type { ResolveItem } from "@/lib/types"

export default function DrugDetailPage() {
  const params = useParams()
  const signature = params.signature as string
  const [drugInfo, setDrugInfo] = useState<ResolveItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDrugInfo = async () => {
      try {
        setLoading(true)
        // Try to resolve the signature to get drug info
        const resolved = await api.resolve(signature, 1)
        const resolvedItems = Array.isArray(resolved) ? resolved : resolved.items
        if (resolvedItems.length > 0) {
          setDrugInfo(resolvedItems[0])

          // Save to recent searches
          const recent = JSON.parse(localStorage.getItem("recent-searches") || "[]")
          const updated = [signature, ...recent.filter((s: string) => s !== signature)].slice(0, 5)
          localStorage.setItem("recent-searches", JSON.stringify(updated))
        } else {
          setError("Drug not found")
        }
      } catch (err) {
        setError("Failed to load drug information")
        console.error("Error loading drug info:", err)
      } finally {
        setLoading(false)
      }
    }

    if (signature) {
      loadDrugInfo()
    }
  }, [signature])

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b bg-card/50 backdrop-blur-sm">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Pill className="h-6 w-6" />
                </div>
                <span className="font-montserrat font-black text-xl">MediBot</span>
              </Link>
              <GlobalSearchBar compact className="w-64" />
            </div>
          </div>
        </header>
        <div className="container mx-auto px-4 py-12 text-center">
          <div className="text-lg text-muted-foreground">Loading drug information...</div>
        </div>
      </div>
    )
  }

  if (error || !drugInfo) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b bg-card/50 backdrop-blur-sm">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Pill className="h-6 w-6" />
                </div>
                <span className="font-montserrat font-black text-xl">MediBot</span>
              </Link>
              <GlobalSearchBar compact className="w-64" />
            </div>
          </div>
        </header>
        <div className="container mx-auto px-4 py-12 text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Drug Not Found</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button asChild>
            <Link href="/">Return to Search</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Pill className="h-6 w-6" />
              </div>
              <span className="font-montserrat font-black text-xl">MediBot</span>
            </Link>

            <div className="flex items-center gap-4">
              <Button variant="outline" size="sm" className="gap-2 bg-transparent">
                <Languages className="h-4 w-4" />
                English
              </Button>
              <GlobalSearchBar compact className="w-64" />
            </div>
          </div>
        </div>
      </header>

      {/* Breadcrumb */}
      <div className="border-b bg-muted/30">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Link href="/" className="hover:text-foreground transition-colors">
              <Home className="h-4 w-4" />
            </Link>
            <ChevronRight className="h-4 w-4" />
            <span className="text-foreground font-medium">{drugInfo.brand_name}</span>
          </div>
        </div>
      </div>

      {/* Drug Hero Section */}
      <div className="bg-gradient-to-r from-primary/5 to-secondary/5 border-b">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl">
            <h1 className="font-montserrat font-black text-3xl text-foreground mb-2">{drugInfo.brand_name}</h1>
            {drugInfo.manufacturer && <p className="text-lg text-muted-foreground mb-4">by {drugInfo.manufacturer}</p>}
            <div className="flex flex-wrap gap-2 mb-4">
              {drugInfo.salts.map((salt, index) => (
                <Badge key={index} variant="secondary">
                  {salt}
                </Badge>
              ))}
            </div>
            {drugInfo.mrp_inr && <div className="text-2xl font-bold text-primary">₹{drugInfo.mrp_inr.toFixed(2)}</div>}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs defaultValue="monograph" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="monograph">Monograph</TabsTrigger>
            <TabsTrigger value="alternatives">Alternatives</TabsTrigger>
            <TabsTrigger value="advise">Advise</TabsTrigger>
          </TabsList>

          <TabsContent value="monograph">
            <MonographTab signature={signature} />
          </TabsContent>

          <TabsContent value="alternatives">
            <AlternativesTab signature={signature} />
          </TabsContent>

          <TabsContent value="advise">
            <AdviseTab signature={signature} drugName={drugInfo.brand_name} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
