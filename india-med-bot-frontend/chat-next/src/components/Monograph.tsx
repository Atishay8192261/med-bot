"use client";
import { useEffect, useState } from "react";
import { monograph } from "@/lib/api";

export default function Monograph({ name, signature }: { name?: string; signature?: string }) {
  const [data, setData] = useState<{
    title: string;
    signature: string;
    sources: string[];
    sections: Record<string, string | string[] | null | undefined>;
    disclaimer: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!name && !signature) return;
    setLoading(true);
    setErr(null);
    monograph(signature, name)
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : "Failed to load monograph"))
      .finally(() => setLoading(false));
  }, [name, signature]);

  const renderSec = (label: string, v?: string | string[] | null) => {
    if (!v) return null;
    return (
      <section className="space-y-1">
        <h4 className="text-sm font-medium text-zinc-800">{label}</h4>
        {Array.isArray(v) ? (
          <ul className="list-disc pl-5 text-sm text-zinc-700">
            {v.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        ) : (
          <p className="whitespace-pre-line text-sm text-zinc-700">{v}</p>
        )}
      </section>
    );
  };

  return (
    <div className="rounded-md border bg-white p-3 text-sm">
      {loading && <div className="text-zinc-600">Loading…</div>}
      {err && <div className="text-red-600">{err}</div>}
      {!loading && !err && (
        <div className="space-y-3">
          {data?.title && <div className="text-base font-semibold">{data.title}</div>}
          <div className="grid gap-3 md:grid-cols-2">
            {renderSec("Uses", data?.sections?.["uses"])}
            {renderSec("How to take", data?.sections?.["how_to_take"])}
            {renderSec("Precautions", data?.sections?.["precautions"])}
            {renderSec("Side effects", data?.sections?.["side_effects"])}
          </div>
          {data?.sources && data.sources.length > 0 && (
            <div className="text-xs text-zinc-500">Sources: {data.sources.join(", ")}</div>
          )}
          {data?.disclaimer && (
            <div className="text-xs text-zinc-500">Disclaimer: {data.disclaimer}</div>
          )}
        </div>
      )}
    </div>
  );
}
