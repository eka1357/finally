"""Chat orchestration: history, LLM, auto-execute actions."""

from __future__ import annotations

import json
import logging
from typing import Any

from .config import settings
from .database import get_connection, new_id, utc_now_iso
from .llm import call_llm
from .market.cache import PriceCache
from .market.interface import MarketDataSource
from .portfolio import TradeError, build_portfolio, execute_trade
from .schemas import ChatResponse
from .watchlist import WatchlistError, add_ticker, get_watchlist, remove_ticker

logger = logging.getLogger(__name__)


def load_history(user_id: str = settings.user_id, limit: int = 20) -> list[dict[str, str]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM chat_messages
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    # Reverse to chronological
    return [{"role": r["role"], "content": r["content"]} for r in reversed(list(rows))]


def save_message(
    role: str,
    content: str,
    actions: dict[str, Any] | None = None,
    user_id: str = settings.user_id,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, role, content, actions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                new_id(),
                user_id,
                role,
                content,
                json.dumps(actions) if actions is not None else None,
                utc_now_iso(),
            ),
        )


async def handle_chat(
    message: str,
    price_cache: PriceCache,
    source: MarketDataSource,
    user_id: str = settings.user_id,
) -> ChatResponse:
    message = message.strip()
    if not message:
        return ChatResponse(message="Please enter a message.", errors=["Empty message"])

    portfolio = build_portfolio(price_cache, user_id)
    watchlist_items = [w.model_dump() for w in get_watchlist(price_cache, user_id)]
    history = load_history(user_id)

    save_message("user", message, user_id=user_id)

    llm = call_llm(message, history, portfolio, watchlist_items)

    trade_results: list[dict[str, Any]] = []
    errors: list[str] = []
    executed_trades: list[dict[str, Any]] = []
    executed_wl: list[dict[str, Any]] = []

    for t in llm.trades:
        try:
            result = execute_trade(price_cache, t.ticker, t.quantity, t.side, user_id)
            executed_trades.append(result.trade or {})
            trade_results.append(
                {
                    "success": True,
                    "message": result.message,
                    "trade": result.trade,
                }
            )
        except TradeError as e:
            errors.append(e.message)
            trade_results.append({"success": False, "message": e.message})

    for change in llm.watchlist_changes:
        try:
            if change.action == "add":
                executed_wl.append(await add_ticker(change.ticker, source, user_id))
            else:
                executed_wl.append(await remove_ticker(change.ticker, source, user_id))
        except WatchlistError as e:
            errors.append(e.message)

    actions = {
        "trades": executed_trades,
        "watchlist_changes": executed_wl,
        "errors": errors,
    }
    save_message("assistant", llm.message, actions=actions, user_id=user_id)

    return ChatResponse(
        message=llm.message,
        trades=executed_trades,
        watchlist_changes=executed_wl,
        trade_results=trade_results,
        errors=errors,
    )


def get_chat_history(user_id: str = settings.user_id, limit: int = 50) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content, actions, created_at
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        actions = None
        if r["actions"]:
            try:
                actions = json.loads(r["actions"])
            except json.JSONDecodeError:
                actions = None
        out.append(
            {
                "role": r["role"],
                "content": r["content"],
                "actions": actions,
                "created_at": r["created_at"],
            }
        )
    return out
