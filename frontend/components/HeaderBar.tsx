"use client";

import { StatusDot } from "./StatusDot";
import { fmtMoney, fmtPct, pnlClass } from "@/lib/format";
import type { ConnectionStatus, Portfolio } from "@/lib/types";

export function HeaderBar({
  portfolio,
  status,
}: {
  portfolio: Portfolio | null;
  status: ConnectionStatus;
}) {
  const total = portfolio?.total_value ?? 10000;
  const cash = portfolio?.cash_balance ?? 10000;
  const pnl = portfolio?.unrealized_pnl ?? 0;
  const ret = portfolio?.total_return_percent ?? 0;

  return (
    <header className="area-header panel flex items-center justify-between px-4">
      <div className="flex items-center gap-4">
        <div className="flex items-baseline gap-2">
          <span className="text-terminal-yellow font-bold tracking-[0.18em] text-sm">
            FINALLY
          </span>
          <span className="text-[10px] text-terminal-muted tracking-widest uppercase">
            Trading Workstation
          </span>
        </div>
        <div className="h-5 w-px bg-terminal-border" />
        <StatusDot status={status} />
      </div>

      <div className="flex items-center gap-6 text-sm">
        <Metric label="Portfolio" value={fmtMoney(total)} emphasize />
        <Metric label="Cash" value={fmtMoney(cash)} />
        <Metric
          label="Unrealized"
          value={fmtMoney(pnl)}
          className={pnlClass(pnl)}
        />
        <Metric
          label="Return"
          value={fmtPct(ret)}
          className={pnlClass(ret)}
        />
      </div>
    </header>
  );
}

function Metric({
  label,
  value,
  className = "",
  emphasize = false,
}: {
  label: string;
  value: string;
  className?: string;
  emphasize?: boolean;
}) {
  return (
    <div className="text-right">
      <div className="text-[10px] uppercase tracking-wider text-terminal-muted">
        {label}
      </div>
      <div
        className={`num ${emphasize ? "text-base font-semibold text-terminal-text" : "text-sm"} ${className}`}
      >
        {value}
      </div>
    </div>
  );
}
