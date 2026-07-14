"use client";

import { fmtMoney, fmtPct, fmtPrice, fmtQty, pnlClass } from "@/lib/format";
import type { Position } from "@/lib/types";

export function PositionsTable({
  positions,
  onSelect,
}: {
  positions: Position[];
  onSelect: (ticker: string) => void;
}) {
  return (
    <section className="area-positions panel flex flex-col min-h-0">
      <div className="panel-header">
        <span className="panel-title">Positions</span>
        <span className="text-[10px] text-terminal-muted num">
          {positions.length}
        </span>
      </div>
      <div className="flex-1 overflow-auto">
        {positions.length === 0 ? (
          <div className="p-4 text-xs text-terminal-muted">
            No open positions. Use the trade bar or AI chat to buy.
          </div>
        ) : (
          <table className="w-full text-[11px]">
            <thead className="sticky top-0 bg-terminal-elevated text-terminal-muted">
              <tr className="text-left">
                <th className="px-2 py-1 font-medium">Ticker</th>
                <th className="px-2 py-1 font-medium text-right">Qty</th>
                <th className="px-2 py-1 font-medium text-right">Avg</th>
                <th className="px-2 py-1 font-medium text-right">Last</th>
                <th className="px-2 py-1 font-medium text-right">P&L</th>
                <th className="px-2 py-1 font-medium text-right">P&L%</th>
                <th className="px-2 py-1 font-medium text-right">Wgt</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr
                  key={p.ticker}
                  onClick={() => onSelect(p.ticker)}
                  className="hover:bg-white/5 cursor-pointer border-t border-terminal-border/50"
                >
                  <td className="px-2 py-1 font-semibold">{p.ticker}</td>
                  <td className="px-2 py-1 text-right num">{fmtQty(p.quantity)}</td>
                  <td className="px-2 py-1 text-right num">{fmtPrice(p.avg_cost)}</td>
                  <td className="px-2 py-1 text-right num">
                    {fmtPrice(p.current_price)}
                  </td>
                  <td className={`px-2 py-1 text-right num ${pnlClass(p.unrealized_pnl)}`}>
                    {fmtMoney(p.unrealized_pnl)}
                  </td>
                  <td
                    className={`px-2 py-1 text-right num ${pnlClass(p.unrealized_pnl_percent)}`}
                  >
                    {fmtPct(p.unrealized_pnl_percent)}
                  </td>
                  <td className="px-2 py-1 text-right num text-terminal-muted">
                    {p.weight != null ? `${p.weight.toFixed(1)}%` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
