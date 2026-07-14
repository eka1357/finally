"use client";

import type { ConnectionStatus } from "@/lib/types";

const map: Record<ConnectionStatus, { color: string; label: string }> = {
  connected: { color: "bg-terminal-green", label: "LIVE" },
  reconnecting: { color: "bg-terminal-yellow animate-pulse-dot", label: "RECONNECT" },
  disconnected: { color: "bg-terminal-red", label: "OFFLINE" },
};

export function StatusDot({ status }: { status: ConnectionStatus }) {
  const s = map[status];
  return (
    <div className="flex items-center gap-2 text-[11px] tracking-wide text-terminal-muted">
      <span className={`inline-block h-2 w-2 rounded-full ${s.color}`} />
      <span className="font-semibold">{s.label}</span>
    </div>
  );
}
