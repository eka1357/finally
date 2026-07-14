"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fmtPrice } from "@/lib/format";
import type { PriceUpdate } from "@/lib/types";

export function ChartPanel({
  ticker,
  history,
  price,
}: {
  ticker: string | null;
  history: number[];
  price: PriceUpdate | undefined;
}) {
  const data = history.map((p, i) => ({ i, price: p }));
  const up =
    history.length >= 2 ? history[history.length - 1] >= history[0] : true;
  const stroke = up ? "#3fb950" : "#f85149";
  const fill = up ? "rgba(63,185,80,0.15)" : "rgba(248,81,73,0.12)";

  return (
    <section className="panel flex flex-col min-h-0 flex-1">
      <div className="panel-header">
        <div className="flex items-center gap-3">
          <span className="panel-title">Chart</span>
          {ticker && (
            <span className="text-sm font-semibold text-terminal-yellow num">
              {ticker}
            </span>
          )}
        </div>
        {price && (
          <div className="flex items-center gap-3 text-sm">
            <span className="num font-semibold">{fmtPrice(price.price)}</span>
            <span
              className={`num text-xs ${price.direction === "up" ? "text-terminal-green" : price.direction === "down" ? "text-terminal-red" : "text-terminal-muted"}`}
            >
              {price.change >= 0 ? "+" : ""}
              {price.change.toFixed(2)} ({price.change_percent.toFixed(2)}%)
            </span>
          </div>
        )}
      </div>
      <div className="flex-1 min-h-0 p-2">
        {!ticker ? (
          <div className="h-full flex items-center justify-center text-terminal-muted text-sm">
            Select a ticker from the watchlist
          </div>
        ) : data.length < 2 ? (
          <div className="h-full flex items-center justify-center text-terminal-muted text-sm">
            Accumulating live ticks for {ticker}…
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={stroke} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={stroke} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#21262d" strokeDasharray="3 3" />
              <XAxis dataKey="i" hide />
              <YAxis
                domain={["auto", "auto"]}
                width={56}
                tick={{ fill: "#8b949e", fontSize: 10 }}
                tickFormatter={(v) => Number(v).toFixed(0)}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: "#161b22",
                  border: "1px solid #30363d",
                  borderRadius: 4,
                  fontSize: 12,
                }}
                labelStyle={{ display: "none" }}
                formatter={(v: number) => [fmtPrice(v), "Price"]}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke={stroke}
                fill={fill}
                strokeWidth={2}
                isAnimationActive={false}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}
