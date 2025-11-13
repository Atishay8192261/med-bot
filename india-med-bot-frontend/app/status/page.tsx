"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Pill, ArrowLeft, Database, Search, Globe, RefreshCw } from "lucide-react"
import Link from "next/link"
import { api } from "@/lib/api-client"
import type { HealthResponse } from "@/lib/types"

export default function StatusPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const loadHealth = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.health()
      setHealth(data)
      setLastUpdated(new Date())
    } catch (err) {
      setError("Failed to load system status")
      console.error("Error loading health:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHealth()
  }, [])

  const getStatusBadge = (status: boolean | string) => {
    if (typeof status === "boolean") {
      return status ? (
        <Badge variant="default" className="bg-green-500">
          OK
        </Badge>
      ) : (
        <Badge variant="destructive">Failed</Badge>
      )
    }

    return status === "ok" ? (
      <Badge variant="default" className="bg-green-500">
        OK
      </Badge>
    ) : (
      <Badge variant="destructive">Failed</Badge>
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
            <Button variant="outline" onClick={loadHealth} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-6">
          <Button variant="outline" asChild>
            <Link href="/">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Link>
          </Button>
        </div>

        <div className="mb-8">
          <h1 className="font-montserrat font-black text-3xl text-foreground mb-2">System Status</h1>
          <p className="text-muted-foreground">Real-time status of MediBot services and dependencies</p>
          {lastUpdated && (
            <p className="text-xs text-muted-foreground mt-2">Last updated: {lastUpdated.toLocaleString()}</p>
          )}
        </div>

        {error && (
          <Card className="mb-6 border-destructive/20 bg-destructive/5">
            <CardContent className="p-4">
              <p className="text-destructive text-sm">{error}</p>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          {/* Overall Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Overall System
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span>System Status</span>
                {loading ? (
                  <Badge variant="secondary">Checking...</Badge>
                ) : health ? (
                  getStatusBadge(health.ok)
                ) : (
                  <Badge variant="destructive">Unknown</Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Database Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Database
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span>Connection</span>
                  {loading ? (
                    <Badge variant="secondary">Checking...</Badge>
                  ) : health ? (
                    getStatusBadge(health.db)
                  ) : (
                    <Badge variant="destructive">Unknown</Badge>
                  )}
                </div>
                {health?.db_error && (
                  <div className="text-xs text-destructive bg-destructive/10 p-2 rounded">Error: {health.db_error}</div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Search Backend */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Search Backend
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span>Search Service</span>
                  {loading ? (
                    <Badge variant="secondary">Checking...</Badge>
                  ) : health ? (
                    getStatusBadge(health.search_ok)
                  ) : (
                    <Badge variant="destructive">Unknown</Badge>
                  )}
                </div>
                {health?.search_backend && (
                  <div className="text-xs text-muted-foreground">Backend: {health.search_backend.toUpperCase()}</div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* External Sources */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                External Sources
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center text-muted-foreground">Checking...</div>
              ) : health?.external ? (
                <div className="space-y-2">
                  {Object.entries(health.external).map(([source, status]) => (
                    <div key={source} className="flex items-center justify-between">
                      <span className="capitalize">{source}</span>
                      {getStatusBadge(status)}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted-foreground">No external sources configured</div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* System Information */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>System Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium mb-2">API Endpoint</h4>
                <code className="text-xs bg-muted p-2 rounded block">
                  {process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"}
                </code>
              </div>
              <div>
                <h4 className="font-medium mb-2">Frontend Version</h4>
                <code className="text-xs bg-muted p-2 rounded block">v1.0.0</code>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
