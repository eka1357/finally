"use client";

import { useEffect, useState } from "react";
import { useAppData } from "@/lib/hooks";
import { HeaderBar } from "./HeaderBar";
import { WatchlistPanel } from "./WatchlistPanel";
import { ChartPanel } from "./ChartPanel";
import { PositionsTable } from "./PositionsTable";
import { PortfolioVisuals } from "./PortfolioVisuals";
import { TradeBar } from "./TradeBar";
import { ChatPanel } from "./ChatPanel";

export function Terminal() {
  const data = useAppData();
  const [selected, setSelected] = useState<string | null>("AAPL");

  useEffect(() => {
    if (!selected && data.watchlist.length > 0) {
      setSelected(data.watchlist[0].ticker);
    }
  }, [data.watchlist, selected]);

  if (data.loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-terminal-bg">
        <div className="text-center">
          <div className="text-terminal-yellow font-bold tracking-[0.2em] mb-2">
            FINALLY
          </div>
          <div className="text-sm text-terminal-muted animate-pulse">
            Booting trading terminal…
          </div>
        </div>
      </div>
    );
  }

  if (data.error && !data.portfolio) {
    return (
      <div className="h-screen flex items-center justify-center bg-terminal-bg p-6">
        <div className="panel max-w-md p-6 text-center">
          <div className="text-terminal-red font-semibold mb-2">
            Backend unreachable
          </div>
          <p className="text-sm text-terminal-muted mb-4">{data.error}</p>
          <p className="text-xs text-terminal-muted">
            Start the API with{" "}
            <code className="text-terminal-yellow">
              uv run uvicorn app.main:app --reload --port 8000
            </code>{" "}
            from <code className="text-terminal-blue">backend/</code>.
          </p>
          <button
            onClick={() => data.refresh()}
            className="mt-4 px-3 py-1.5 text-xs bg-terminal-purple rounded-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const hist = selected ? data.history[selected] || [] : [];
  const price = selected ? data.prices[selected] : undefined;

  return (
    <div className="terminal-grid">
      <HeaderBar portfolio={data.portfolio} status={data.status} />

      <WatchlistPanel
        items={data.watchlist}
        history={data.history}
        flash={data.flash}
        selected={selected}
        onSelect={setSelected}
        onAdd={data.addTicker}
        onRemove={data.removeTicker}
      />

      <div className="area-main flex flex-col min-h-0 gap-0">
        <div className="flex-1 min-h-0 flex flex-col">
          <ChartPanel ticker={selected} history={hist} price={price} />
        </div>
        <div className="panel border-t-0 rounded-t-none">
          <TradeBar
            defaultTicker={selected}
            busy={data.busy}
            onTrade={data.trade}
          />
        </div>
      </div>

      <ChatPanel
        messages={data.messages}
        busy={data.busy}
        onSend={data.sendChat}
      />

      <PositionsTable
        positions={data.portfolio?.positions || []}
        onSelect={setSelected}
      />

      <PortfolioVisuals
        portfolio={data.portfolio}
        snapshots={data.snapshots}
      />
    </div>
  );
}
