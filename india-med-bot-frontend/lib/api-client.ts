import type {
  SearchResponse,
  ResolveItem,
  MonographResponse,
  AlternativesResponse,
  AdviseResponse,
  HealthResponse,
} from "./types"

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"

async function getJSON<T>(path: string, params?: Record<string, string | number | boolean>): Promise<T> {
  const url = new URL(path, API_BASE)
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)))
  }
  const r = await fetch(url.toString(), { cache: "no-store" })
  if (!r.ok) throw new Error(`GET ${url} -> ${r.status}`)
  return r.json() as Promise<T>
}

export const api = {
  search: (query: string, limit = 10) => getJSON<SearchResponse>("/search", { query, limit }),
  resolve: (name: string, limit = 10) => getJSON<ResolveItem[] | { items: ResolveItem[] }>("/resolve", { name, limit }),
  monographBySignature: (signature: string) => getJSON<MonographResponse>("/monograph", { signature }),
  monographByName: (name: string) => getJSON<MonographResponse>("/monograph", { name }),
  alternativesBySignature: (signature: string) => getJSON<AlternativesResponse>("/alternatives", { signature }),
  alternativesByName: (name: string) => getJSON<AlternativesResponse>("/alternatives", { name }),
  advise: (opts: { signature?: string; name?: string; query?: string; intent?: string; lang?: "en" | "hi" }) =>
    getJSON<AdviseResponse>("/advise", opts as any),
  health: () => getJSON<HealthResponse>("/health"),
}
