"use client";
import { useState } from "react";
import { advise, type AdviseIntent, type AdvisePayload } from "@/lib/api";

export type ChatProps = {
  name?: string;
  signature?: string;
};

type Msg = { role: "user" | "assistant"; content: string };

const INTENTS: { key: AdviseIntent; label: string }[] = [
  { key: "summary", label: "Summary" },
  { key: "uses", label: "Uses" },
  { key: "side_effects", label: "Side effects" },
  { key: "how_to_take", label: "How to take" },
  { key: "precautions", label: "Precautions" },
  { key: "cheaper", label: "Cheaper" },
];

export default function Chat({ name, signature }: ChatProps) {
  const [q, setQ] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const disabled = !name && !signature;

  const send = async (opts?: { intent?: AdviseIntent }) => {
    if (disabled) return;
    const userText = q.trim() || opts?.intent || "";
    if (!userText && !opts?.intent) return;
    const newMsgs = [...msgs, { role: "user", content: userText }];
    setMsgs(newMsgs);
    setQ("");
    setBusy(true);
    try {
      const resp: AdvisePayload = await advise({ name, signature, query: userText, intent: opts?.intent });
      const a = resp.answer || "No answer.";
      setMsgs((m) => [...m, { role: "assistant", content: a }]);
    } catch (e: any) {
      setMsgs((m) => [...m, { role: "assistant", content: `Error: ${e?.message ?? "advise failed"}` }]);
    } finally {
      setBusy(false);
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await send();
  };

  return (
    <div className="rounded-md border bg-white">
      <div className="flex flex-wrap gap-2 border-b p-2">
        {INTENTS.map((i) => (
          <button
            key={i.key}
            disabled={disabled || busy}
            onClick={() => send({ intent: i.key })}
            className="rounded-md border px-2 py-1 text-xs hover:bg-zinc-50 disabled:opacity-50"
          >
            {i.label}
          </button>
        ))}
      </div>
      <div className="max-h-[50vh] space-y-2 overflow-auto p-3 text-sm">
        {msgs.length === 0 && (
          <div className="text-zinc-500">Ask a question or click a quick intent to begin.</div>
        )}
        {msgs.map((m, idx) => (
          <div key={idx} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={
                "inline-block rounded-md px-3 py-2 " +
                (m.role === "user" ? "bg-black text-white" : "bg-zinc-100 text-zinc-900")
              }
            >
              {m.content}
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={onSubmit} className="flex items-center gap-2 border-t p-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={disabled ? "Select a brand above to chat" : "Type your question…"}
          disabled={disabled || busy}
          className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-zinc-500 disabled:opacity-50"
        />
        <button
          disabled={disabled || busy}
          className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
