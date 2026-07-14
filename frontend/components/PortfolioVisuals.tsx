"use client";

import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  Treemap,
  XAxis,
  YAxis,
} from "recharts";
import { fmtMoney } from "@/lib/format";
import type { Portfolio, Snapshot } from "@/lib/types";

function pnlColor(pnl: number | null | undefined): string {
  if (pnl == null || pnl === 0) return "#484f58";
  if (pnl > 0) return "#238636";
  return "#da3633";
}

export function PortfolioVisuals({
  portfolio,
  snapshots,
}: {
  portfolio: Portfolio | null;
  snapshots: Snapshot[];
}) {
  const treeData =
    portfolio?.positions
      .filter((p) => (p.market_value ?? 0) > 0)
      .map((p) => ({
        name: p.ticker,
        size: Math.max(p.market_value || 0, 1),
        pnl: p.unrealized_pnl ?? 0,
      })) || [];

  const cashLeaf = portfolio
    ? {
        name: "CASH",
        size: Math.max(portfolio.cash_balance, 1),
        pnl: 0,
      }
    : null;

  const treemapData = cashLeaf ? [...treeData, cashLeaf] : treeData;

  const hist = snapshots.map((s, i) => ({
    i,
    value: s.total_value,
    t: s.recorded_at,
  }));

  return (
    <section className="area-bottom panel grid grid-cols-2 min-h-0">
      <div className="flex flex-col min-h-0 border-r border-terminal-border">
        <div className="panel-header">
          <span className="panel-title">Heatmap</span>
        </div>
        <div className="flex-1 min-h-0 p-1">
          {treemapData.length === 0 ? (
            <Empty label="No holdings yet" />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <Treemap
                data={treemapData}
                dataKey="size"
                nameKey="name"
                stroke="#0d1117"
                content={<HeatCell />}
                isAnimationActive={false}
              />
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="flex flex-col min-h-0">
        <div className="panel-header">
          <span className="panel-title">Portfolio Value</span>
          {portfolio && (
            <span className="text-xs num text-terminal-blue">
              {fmtMoney(portfolio.total_value)}
            </span>
          )}
        </div>
        <div className="flex-1 min-h-0 p-2">
          {hist.length < 2 ? (
            <Empty label="Building P&L history…" />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hist} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <XAxis dataKey="i" hide />
                <YAxis
                  domain={["auto", "auto"]}
                  width={48}
                  tick={{ fill: "#8b949e", fontSize: 10 }}
                  tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "#161b22",
                    border: "1px solid #30363d",
                    fontSize: 12,
                  }}
                  labelStyle={{ display: "none" }}
                  formatter={(v: number) => [fmtMoney(v), "Value"]}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#209dd7"
                  fill="rgba(32,157,215,0.18)"
                  strokeWidth={2}
                  isAnimationActive={false}
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </section>
  );
}

function Empty({ label }: { label: string }) {
  return (
    <div className="h-full flex items-center justify-center text-xs text-terminal-muted">
      {label}
    </div>
  );
}

function HeatCell(props: {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  depth?: number;
  pnl?: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}) {
  const { x = 0, y = 0, width = 0, height = 0, name, depth, pnl } = props;
  if (depth !== 1) return null;
  if (width < 4 || height < 4) return null;
  const fill = pnlColor(typeof pnl === "number" ? pnl : 0);
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={fill}
        stroke="#0d1117"
        strokeWidth={2}
        rx={2}
      />
      {width > 36 && height > 22 && (
        <text x={x + 6} y={y + 16} fill="#e6edf3" fontSize={11} fontWeight={600}>
          {name}
        </text>
      )}
      {width > 48 && height > 36 && typeof pnl === "number" && name !== "CASH" && (
        <text x={x + 6} y={y + 30} fill="#c9d1d9" fontSize={10}>
          {pnl >= 0 ? "+" : ""}
          {pnl.toFixed(0)}
        </text>
      )}
    </g>
  );
}
