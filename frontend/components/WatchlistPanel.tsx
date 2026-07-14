"use client";

import { useState } from "react";
import { Sparkline } from "./Sparkline";
import { fmtPct, fmtPrice, pnlClass } from "@/lib/format";
import type { WatchlistItem } from "@/lib/types";

export function WatchlistPanel({
  items,
  history,
  flash,
  selected,
  onSelect,
  onAdd,
  onRemove,
}: {
  items: WatchlistItem[];
  history: Record<string, number[]>;
  flash: Record<string, "up" | "down">;
  selected: string | null;
  onSelect: (ticker: string) => void;
  onAdd: (ticker: string) => Promise<void>;
  onRemove: (ticker: string) => Promise<void>;
}) {
  const [ticker, setTicker] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    const t = ticker.trim().toUpperCase();
    if (!t) return;
    setErr(null);
    try {
      await onAdd(t);
      setTicker("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed");
    }
  };

  return (
    <section className="area-watchlist panel flex flex-col min-h-0">
      <div className="panel-header">
        <span className="panel-title">Watchlist</span>
        <span className="text-[10px] text-terminal-muted num">{items.length}</span>
      </div>

      <div className="flex gap-1 px-2 py-2 border-b border-terminal-border">
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="ADD TICKER"
          className="flex-1 bg-terminal-bg border border-terminal-border rounded-sm px-2 py-1 text-xs num focus:outline-none focus:border-terminal-blue"
        />
        <button
          onClick={submit}
          className="px-2 py-1 text-xs font-semibold rounded-sm bg-terminal-purple text-white hover:brightness-110"
        >
          ADD
        </button>
      </div>
      {err && (
        <div className="px-2 py-1 text-[11px] text-terminal-red border-b border-terminal-border">
          {err}
        </div>
      )}

      <div className="flex-1 overflow-auto">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-terminal-elevated text-terminal-muted">
            <tr className="text-left">
              <th className="px-2 py-1.5 font-medium">Sym</th>
              <th className="px-2 py-1.5 font-medium text-right">Last</th>
              <th className="px-2 py-1.5 font-medium text-right">Chg%</th>
              <th className="px-2 py-1.5 font-medium">Spark</th>
              <th className="w-6" />
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const f = flash[item.ticker];
              const flashCls =
                f === "up"
                  ? "animate-flash-up"
                  : f === "down"
                    ? "animate-flash-down"
                    : "";
              const selectedCls =
                selected === item.ticker
                  ? "bg-terminal-blue/10 border-l-2 border-l-terminal-yellow"
                  : "border-l-2 border-l-transparent";
              const hist = history[item.ticker] || [];
              const up =
                hist.length >= 2 ? hist[hist.length - 1] >= hist[0] : true;

              return (
                <tr
                  key={item.ticker}
                  onClick={() => onSelect(item.ticker)}
                  className={`cursor-pointer hover:bg-white/5 ${selectedCls} ${flashCls}`}
                >
                  <td className="px-2 py-1.5 font-semibold text-terminal-text">
                    {item.ticker}
                  </td>
                  <td className={`px-2 py-1.5 text-right num ${pnlClass(item.change)}`}>
                    {fmtPrice(item.price)}
                  </td>
                  <td
                    className={`px-2 py-1.5 text-right num ${pnlClass(item.change_percent)}`}
                  >
                    {fmtPct(item.change_percent)}
                  </td>
                  <td className="px-1 py-1">
                    <Sparkline values={hist} positive={up} />
                  </td>
                  <td className="pr-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemove(item.ticker);
                      }}
                      className="text-terminal-muted hover:text-terminal-red text-[10px] px-1"
                      title="Remove"
                    >
                      ×
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
