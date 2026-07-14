"use client";

import { useEffect, useState } from "react";

export function TradeBar({
  defaultTicker,
  busy,
  onTrade,
}: {
  defaultTicker: string | null;
  busy: boolean;
  onTrade: (ticker: string, qty: number, side: "buy" | "sell") => Promise<string>;
}) {
  const [ticker, setTicker] = useState(defaultTicker || "AAPL");
  const [qty, setQty] = useState("10");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (defaultTicker) setTicker(defaultTicker);
  }, [defaultTicker]);

  const run = async (side: "buy" | "sell") => {
    setMsg(null);
    setErr(null);
    const q = Number(qty);
    if (!ticker.trim() || !(q > 0)) {
      setErr("Enter ticker and positive quantity");
      return;
    }
    try {
      const m = await onTrade(ticker.trim().toUpperCase(), q, side);
      setMsg(m);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Trade failed");
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 px-3 py-2 border-t border-terminal-border bg-terminal-elevated/60">
      <span className="text-[10px] uppercase tracking-wider text-terminal-muted mr-1">
        Trade
      </span>
      <input
        value={ticker}
        onChange={(e) => setTicker(e.target.value.toUpperCase())}
        onFocus={() => {
          if (defaultTicker) setTicker(defaultTicker);
        }}
        className="w-20 bg-terminal-bg border border-terminal-border rounded-sm px-2 py-1 text-xs num focus:outline-none focus:border-terminal-yellow"
        placeholder="TICKER"
      />
      <input
        value={qty}
        onChange={(e) => setQty(e.target.value)}
        className="w-20 bg-terminal-bg border border-terminal-border rounded-sm px-2 py-1 text-xs num focus:outline-none focus:border-terminal-yellow"
        placeholder="QTY"
      />
      <button
        disabled={busy}
        onClick={() => run("buy")}
        className="px-3 py-1 text-xs font-bold rounded-sm bg-terminal-green/90 text-black hover:brightness-110 disabled:opacity-50"
      >
        BUY
      </button>
      <button
        disabled={busy}
        onClick={() => run("sell")}
        className="px-3 py-1 text-xs font-bold rounded-sm bg-terminal-red/90 text-white hover:brightness-110 disabled:opacity-50"
      >
        SELL
      </button>
      {msg && <span className="text-[11px] text-terminal-green">{msg}</span>}
      {err && <span className="text-[11px] text-terminal-red">{err}</span>}
      <span className="ml-auto text-[10px] text-terminal-muted">
        Market orders · instant fill · no fees
      </span>
    </div>
  );
}
