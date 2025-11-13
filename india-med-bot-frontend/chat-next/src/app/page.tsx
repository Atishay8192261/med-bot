"use client";
import { useEffect, useState } from "react";
import { API_BASE, health, search, type SearchHit } from "@/lib/api";
import Chat from "@/components/Chat";
import Monograph from "@/components/Monograph";
import Alternatives from "@/components/Alternatives";

export default function Home() {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [selected, setSelected] = useState<SearchHit | null>(null);
  const [tab, setTab] = useState<"Chat" | "Monograph" | "Alternatives">("Chat");

  useEffect(() => {
    health()
      .then((h) => setHealthy(Boolean(h?.ok)))
      .catch(() => setHealthy(false));
  }, []);

  const onSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const res = await search(q, 8);
      setHits(res.hits || []);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Search failed";
      setErr(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <h1 className="text-lg font-semibold">India Med Bot</h1>
          <div className="text-xs text-zinc-500">API: {API_BASE}</div>
        </div>
      </header>
  <main className="mx-auto max-w-6xl px-4 py-6">
        {healthy === false && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Backend not healthy. Please ensure API at {API_BASE} is running.
          </div>
        )}
        <form onSubmit={onSearch} className="mb-6 flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search brands, e.g. para"
            className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
          <button
            disabled={loading}
            className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </form>
        {err && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {err}
          </div>
        )}
  <div className="grid gap-6 md:grid-cols-2">
  <ul className="divide-y rounded-md border bg-white md:max-h-[70vh] md:overflow-auto">
          {hits.map((h) => (
            <li
              key={`${h.id}-${h.brand_name}`}
              className={`cursor-pointer p-3 hover:bg-zinc-50 ${
                selected?.salt_signature === h.salt_signature ? "bg-zinc-50" : ""
              }`}
              onClick={() => setSelected(h)}
            >
              <div className="flex items-center justify-between">
                <div className="font-medium">{h.brand_name}</div>
                {h.mrp_inr != null && (
                  <div className="text-sm text-zinc-600">₹ {h.mrp_inr}</div>
                )}
              </div>
              <div className="mt-1 text-sm text-zinc-600">
                {h.manufacturer}
              </div>
              <div className="mt-1 text-xs text-zinc-500">
                {h.salts?.join(" · ")}
              </div>
            </li>
          ))}
          {!loading && hits.length === 0 && (
            <li className="p-3 text-sm text-zinc-600">No results.</li>
          )}
          {loading && (
            <li className="p-3 text-sm text-zinc-600">Loading…</li>
          )}
        </ul>

        <div>
          <div className="mb-3 flex items-center justify-between">
            <div className="text-sm text-zinc-700">
              {selected ? (
                <>
                  Selected: <span className="font-medium">{selected.brand_name}</span>
                  {selected.salt_signature ? (
                    <span className="ml-2 text-zinc-500">sig {selected.salt_signature}</span>
                  ) : null}
                </>
              ) : (
                <span>Select a brand to enable chat and details.</span>
              )}
            </div>
          </div>
          {/* Tabs */}
          <div className="mb-3 flex gap-2">
            {(["Chat","Monograph","Alternatives"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`rounded-md border px-3 py-1 text-sm ${tab===t?"bg-black text-white":"bg-white hover:bg-zinc-50"}`}
                disabled={!selected}
              >
                {t}
              </button>
            ))}
          </div>
          {tab === "Chat" && <Chat name={selected?.brand_name} signature={selected?.salt_signature} />}
          {tab === "Monograph" && <Monograph name={selected?.brand_name} signature={selected?.salt_signature} />}
          {tab === "Alternatives" && <Alternatives name={selected?.brand_name} signature={selected?.salt_signature} />}
        </div>
        </div>
      </main>
    </div>
  );
}
