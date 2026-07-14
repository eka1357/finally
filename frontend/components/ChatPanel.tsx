"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "@/lib/types";

export function ChatPanel({
  messages,
  busy,
  onSend,
}: {
  messages: ChatMessage[];
  busy: boolean;
  onSend: (text: string) => Promise<unknown>;
}) {
  const [text, setText] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const submit = async () => {
    const t = text.trim();
    if (!t || busy) return;
    setText("");
    await onSend(t);
  };

  return (
    <section className="area-chat panel flex flex-col min-h-0">
      <div className="panel-header">
        <span className="panel-title">AI Assistant</span>
        <span className="text-[10px] text-terminal-yellow tracking-wider">
          FINALLY COPILOT
        </span>
      </div>

      <div className="flex-1 overflow-auto px-3 py-2 space-y-3">
        {messages.length === 0 && (
          <div className="text-xs text-terminal-muted leading-relaxed">
            <p className="mb-2 text-terminal-text font-medium">
              Ask FinAlly to analyze or trade.
            </p>
            <ul className="space-y-1 list-disc list-inside">
              <li>Summarize my portfolio</li>
              <li>Buy 5 AAPL</li>
              <li>Add AMD to watchlist</li>
              <li>What&apos;s my risk concentration?</li>
            </ul>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`text-xs leading-relaxed ${
              m.role === "user" ? "text-right" : "text-left"
            }`}
          >
            <div
              className={`inline-block max-w-[95%] rounded-sm px-2.5 py-2 ${
                m.role === "user"
                  ? "bg-terminal-blue/20 border border-terminal-blue/30 text-terminal-text"
                  : "bg-terminal-elevated border border-terminal-border text-terminal-text"
              }`}
            >
              <div className="text-[9px] uppercase tracking-wider text-terminal-muted mb-1">
                {m.role === "user" ? "You" : "FinAlly"}
              </div>
              <div className="whitespace-pre-wrap">{m.content}</div>
              {m.actions && (
                <div className="mt-2 space-y-1 border-t border-terminal-border pt-2">
                  {(m.actions.trades || []).map((t, j) => (
                    <div
                      key={`t${j}`}
                      className="text-[10px] text-terminal-green num"
                    >
                      ✓ Trade: {JSON.stringify(t)}
                    </div>
                  ))}
                  {(m.actions.watchlist_changes || []).map((w, j) => (
                    <div
                      key={`w${j}`}
                      className="text-[10px] text-terminal-blue num"
                    >
                      ✓ Watchlist: {JSON.stringify(w)}
                    </div>
                  ))}
                  {(m.actions.errors || []).map((e, j) => (
                    <div key={`e${j}`} className="text-[10px] text-terminal-red">
                      ! {e}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="text-xs text-terminal-muted animate-pulse">
            FinAlly is thinking…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-terminal-border p-2 flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && submit()}
          disabled={busy}
          placeholder="Message FinAlly…"
          className="flex-1 bg-terminal-bg border border-terminal-border rounded-sm px-2 py-1.5 text-xs focus:outline-none focus:border-terminal-purple disabled:opacity-50"
        />
        <button
          onClick={submit}
          disabled={busy || !text.trim()}
          className="px-3 py-1.5 text-xs font-semibold rounded-sm bg-terminal-purple text-white hover:brightness-110 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </section>
  );
}
