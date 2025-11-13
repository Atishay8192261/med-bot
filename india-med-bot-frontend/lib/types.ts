export interface ResolveItem {
  id?: number
  brand_name: string
  manufacturer?: string | null
  mrp_inr?: number | null
  salt_signature?: string | null
  salts: string[]
}

export interface SearchResponse {
  query: string
  hits: ResolveItem[]
}

export interface MonographSections {
  uses?: string[]
  how_to_take?: string[]
  precautions?: string[]
  side_effects?: string[]
}

export interface MonographResponse {
  title?: string
  sections: MonographSections
  sources?: { name: string; url: string }[]
  disclaimer: string
}

export interface AlternativesPriceSummary {
  min?: number | null
  q1?: number | null
  median?: number | null
  q3?: number | null
  max?: number | null
  count?: number | null
}

export interface AlternativeBrand {
  brand_name: string
  manufacturer?: string | null
  mrp_inr?: number | null
  pack?: string | null
  dosage_form?: string | null
  salt_signature?: string | null
  sources?: string[]
}

export interface AlternativesResponse {
  brands: AlternativeBrand[]
  janaushadhi?: AlternativeBrand[]
  nppa_ceiling_price?: number | null
  price_summary?: AlternativesPriceSummary
  disclaimer: string
}

export interface AdviseResponse {
  intent: string
  signature?: string | null
  salts: string[]
  answer: string
  sources?: { name: string; url: string }[]
  alternatives?: AlternativesResponse
  disclaimer: string
}

export interface HealthResponse {
  ok: boolean
  db: boolean
  db_error?: string | null
  search_backend: "os" | "pg"
  search_ok: boolean
  external?: Record<string, "ok" | "fail">
}
