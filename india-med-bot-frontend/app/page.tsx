"use client"

import { useState, useEffect } from "react"
import { GlobalSearchBar } from "@/components/global-search-bar"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Pill, Search, Clock, Languages } from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function HomePage() {
  const [recentSearches, setRecentSearches] = useState<string[]>([])
  const router = useRouter()

  // Load recent searches from localStorage
  useEffect(() => {
    const recent = localStorage.getItem("recent-searches")
    if (recent) {
      setRecentSearches(JSON.parse(recent).slice(0, 5))
    }
  }, [])

  const handleRecentClick = (signature: string) => {
    router.push(`/drug/${signature}`)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Pill className="h-6 w-6" />
              </div>
              <div>
                <h1 className="font-montserrat font-black text-xl text-foreground">MediBot</h1>
                <p className="text-xs text-muted-foreground">Indian Medicine Assistant</p>
              </div>
            </div>

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

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        <div className="mx-auto max-w-2xl text-center">
          {/* Hero Section */}
          <div className="mb-12">
            <h2 className="font-montserrat font-black text-4xl text-foreground mb-4">Find Medicine Information</h2>
            <p className="text-lg text-muted-foreground mb-8">
              Search for drug details, alternatives, and get AI-powered medical advice in Hindi and English
            </p>

            {/* Main Search */}
            <Card className="p-6 shadow-lg">
              <CardContent className="p-0">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                  <GlobalSearchBar
                    className="w-full"
                    placeholder="Search for medicine brands like Augmentin, Paracetamol..."
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Searches */}
          {recentSearches.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <h3 className="font-montserrat font-semibold text-foreground">Recent Searches</h3>
              </div>
              <div className="flex flex-wrap gap-2 justify-center">
                {recentSearches.map((search, index) => (
                  <Badge
                    key={index}
                    variant="secondary"
                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                    onClick={() => handleRecentClick(search)}
                  >
                    {search}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <Card className="p-6 text-center hover:shadow-lg transition-shadow">
              <CardContent className="p-0">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Search className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-montserrat font-semibold mb-2">Smart Search</h3>
                <p className="text-sm text-muted-foreground">
                  Find medicines by brand name with intelligent autocomplete
                </p>
              </CardContent>
            </Card>

            <Card className="p-6 text-center hover:shadow-lg transition-shadow">
              <CardContent className="p-0">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Pill className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-montserrat font-semibold mb-2">Drug Information</h3>
                <p className="text-sm text-muted-foreground">
                  Comprehensive monographs with uses, dosage, and precautions
                </p>
              </CardContent>
            </Card>

            <Card className="p-6 text-center hover:shadow-lg transition-shadow">
              <CardContent className="p-0">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Languages className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-montserrat font-semibold mb-2">AI Advice</h3>
                <p className="text-sm text-muted-foreground">Get personalized medical advice in Hindi and English</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-card/50 mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Pill className="h-4 w-4" />
              </div>
              <span className="font-montserrat font-semibold">MediBot</span>
            </div>
            <div className="flex gap-6 text-sm text-muted-foreground">
              <Link href="/legal/disclaimer" className="hover:text-foreground transition-colors">
                Disclaimer
              </Link>
              <Link href="/status" className="hover:text-foreground transition-colors">
                System Status
              </Link>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t text-center text-xs text-muted-foreground">
            This tool provides information for educational purposes only. Always consult healthcare professionals for
            medical advice.
          </div>
        </div>
      </footer>
    </div>
  )
}
