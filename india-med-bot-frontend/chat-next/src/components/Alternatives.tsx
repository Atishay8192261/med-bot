"use client";
import { useEffect, useState } from "react";
import { alternatives } from "@/lib/api";

export default function Alternatives({ name, signature }: { name?: string; signature?: string }) {
  const [data, setData] = useState<{
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
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!name && !signature) return;
    setLoading(true);
    setErr(null);
    alternatives(signature, name)
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : "Failed to load alternatives"))
      .finally(() => setLoading(false));
  }, [name, signature]);

  return (
    <div className="rounded-md border bg-white p-3 text-sm">
      {loading && <div className="text-zinc-600">Loading…</div>}
      {err && <div className="text-red-600">{err}</div>}
      {!loading && !err && data && (
        <div className="space-y-3">
          {data.price_summary && (
            <div className="rounded-md border p-3">
              <div className="font-medium">Price summary</div>
              <div className="mt-1 grid grid-cols-2 gap-2 text-xs text-zinc-700 md:grid-cols-4">
                <div>Min: ₹ {data.price_summary.min_price ?? "-"}</div>
                <div>Median: ₹ {data.price_summary.median ?? "-"}</div>
                <div>Max: ₹ {data.price_summary.max_price ?? "-"}</div>
                <div>Count: {data.price_summary.count ?? "-"}</div>
              </div>
              {data.price_summary.nppa_ceiling != null && (
                <div className="mt-1 text-xs text-zinc-600">NPPA ceiling: ₹ {data.price_summary.nppa_ceiling}</div>
              )}
            </div>
          )}

          {data.janaushadhi && data.janaushadhi.length > 0 && (
            <div>
              <div className="font-medium">Jan Aushadhi options</div>
              <ul className="mt-2 divide-y rounded-md border">
                {data.janaushadhi.map((j, i) => (
                  <li key={i} className="p-2">
                    <div className="flex items-center justify-between">
                      <div>{j.generic_name}</div>
                      {j.mrp_inr != null && <div>₹ {j.mrp_inr}</div>}
                    </div>
                    <div className="text-xs text-zinc-600">
                      {[j.strength, j.dosage_form, j.pack].filter(Boolean).join(" · ")}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.brands && data.brands.length > 0 && (
            <div>
              <div className="font-medium">Other brands</div>
              <ul className="mt-2 divide-y rounded-md border">
                {data.brands.slice(0, 25).map((b) => (
                  <li key={b.id} className="p-2">
                    <div className="flex items-center justify-between">
                      <div>{b.brand_name}</div>
                      {b.mrp_inr != null && <div>₹ {b.mrp_inr}</div>}
                    </div>
                    <div className="text-xs text-zinc-600">{b.manufacturer}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.disclaimer && (
            <div className="text-xs text-zinc-500">Disclaimer: {data.disclaimer}</div>
          )}
        </div>
      )}
    </div>
  );
}
