export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export type SearchHit = {
  id?: number;
  brand_name: string;
  mrp_inr?: number;
  manufacturer?: string;
  salt_signature?: string;
  salts: string[];
};

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, { ...init, cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} ${res.status}`);
  return res.json();
}

export async function health() {
  return apiGet<any>(`/health`);
}

export async function search(query: string, limit = 5) {
  const p = new URLSearchParams({ query, limit: String(limit) });
  return apiGet<{ query: string; hits: SearchHit[] }>(`/search?${p.toString()}`);
}

export type AdviseIntent = "uses" | "side_effects" | "how_to_take" | "precautions" | "cheaper" | "summary";

export type AdvisePayload = {
  intent: AdviseIntent;
  signature: string;
  brand?: string | null;
  salts: string[];
  answer: string;
  sources: string[];
  disclaimer: string;
};

export async function advise(opts: { name?: string; signature?: string; query?: string; intent?: AdviseIntent }) {
  const p = new URLSearchParams();
  if (opts.name) p.set("name", opts.name);
  if (opts.signature) p.set("signature", opts.signature);
  if (opts.query) p.set("query", opts.query);
  if (opts.intent) p.set("intent", opts.intent);
  return apiGet<AdvisePayload>(`/advise?${p.toString()}`);
}

export async function monograph(signature?: string, name?: string) {
  const p = new URLSearchParams();
  if (signature) p.set("signature", signature);
  if (name) p.set("name", name);
  return apiGet<{
    title: string;
    signature: string;
    sources: string[];
    sections: Record<string, string | string[] | null | undefined>;
    disclaimer: string;
  }>(`/monograph?${p.toString()}`);
}

export async function alternatives(signature?: string, name?: string) {
  const p = new URLSearchParams();
  if (signature) p.set("signature", signature);
  if (name) p.set("name", name);
  return apiGet<{
    signature: string;
    salts: { salt_pos: number; salt_name: string }[];
    brands: { id: number; brand_name: string; manufacturer?: string; mrp_inr?: number | null }[];
    janaushadhi: { generic_name: string; strength?: string; dosage_form?: string; pack?: string; mrp_inr?: number | null }[];
    nppa_ceiling_price?: number | null;
    price_summary?: {
      min_price?: number;
      q1?: number;
      median?: number;
      q3?: number;
      max_price?: number;
      count?: number;
      n_brands?: number;
      n_jana?: number;
      nppa_ceiling?: number | null;
    } | null;
    disclaimer: string;
  }>(`/alternatives?${p.toString()}`);
}
