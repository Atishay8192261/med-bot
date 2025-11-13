"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Search, X } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { api } from "@/lib/api-client"
import type { ResolveItem } from "@/lib/types"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"

interface GlobalSearchBarProps {
  className?: string
  placeholder?: string
  compact?: boolean
}

export function GlobalSearchBar({
  className,
  placeholder = "Search a medicine brand…",
  compact = false,
}: GlobalSearchBarProps) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<ResolveItem[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const router = useRouter()
  const searchRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setIsOpen(false)
      return
    }

    const timeoutId = setTimeout(async () => {
      setIsLoading(true)
      try {
        const response = await api.search(query, 8)
        setResults(response.hits)
        setIsOpen(true)
        setSelectedIndex(-1)
      } catch (error) {
        console.error("Search error:", error)
        setResults([])
      } finally {
        setIsLoading(false)
      }
    }, 200)

    return () => clearTimeout(timeoutId)
  }, [query])

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1))
        break
      case "ArrowUp":
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, -1))
        break
      case "Enter":
        e.preventDefault()
        if (selectedIndex >= 0 && results[selectedIndex]) {
          handleSelectResult(results[selectedIndex])
        }
        break
      case "Escape":
        setIsOpen(false)
        setSelectedIndex(-1)
        inputRef.current?.blur()
        break
    }
  }

  const handleSelectResult = (item: ResolveItem) => {
    if (item.salt_signature) {
      router.push(`/drug/${item.salt_signature}`)
    } else {
      // If no signature, resolve first then navigate
      api.resolve(item.brand_name, 1).then((resolved) => {
        const resolvedItems = Array.isArray(resolved) ? resolved : resolved.items
        if (resolvedItems[0]?.salt_signature) {
          router.push(`/drug/${resolvedItems[0].salt_signature}`)
        }
      })
    }
    setQuery("")
    setIsOpen(false)
    setSelectedIndex(-1)
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSelectedIndex(-1)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <div ref={searchRef} className={cn("relative", className)}>
      <div className="relative">
        
        <Input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className={cn("pl-10 pr-10", compact ? "h-9" : "h-11")}
        />
        {query && (
          <Button
            variant="ghost"
            size="sm"
            className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2 p-0"
            onClick={() => {
              setQuery("")
              setIsOpen(false)
              setSelectedIndex(-1)
            }}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && (
        <Card className="absolute top-full z-50 mt-1 w-full border bg-popover p-0 shadow-lg">
          {isLoading ? (
            <div className="p-4 text-center text-sm text-muted-foreground">Loading…</div>
          ) : results.length > 0 ? (
            <div className="max-h-80 overflow-y-auto">
              {results.map((item, index) => (
                <button
                  key={`${item.brand_name}-${index}`}
                  className={cn(
                    "w-full px-4 py-3 text-left hover:bg-accent hover:text-accent-foreground",
                    "border-b border-border last:border-b-0",
                    selectedIndex === index && "bg-accent text-accent-foreground",
                  )}
                  onClick={() => handleSelectResult(item)}
                >
                  <div className="font-medium">{item.brand_name}</div>
                  {item.manufacturer && <div className="text-sm text-muted-foreground">{item.manufacturer}</div>}
                  {item.salts.length > 0 && (
                    <div className="text-xs text-muted-foreground">{item.salts.join(", ")}</div>
                  )}
                </button>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-sm text-muted-foreground">No results found</div>
          )}
        </Card>
      )}
    </div>
  )
}
