"""Watchlist management."""

from __future__ import annotations

from typing import Any

from .config import settings
from .database import get_connection, new_id, utc_now_iso
from .market.cache import PriceCache
from .market.interface import MarketDataSource
from .schemas import WatchlistItem


class WatchlistError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def list_tickers(user_id: str = settings.user_id) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ticker FROM watchlist
            WHERE user_id = ?
            ORDER BY added_at ASC
            """,
            (user_id,),
        ).fetchall()
        return [r["ticker"] for r in rows]


def get_watchlist(price_cache: PriceCache, user_id: str = settings.user_id) -> list[WatchlistItem]:
    items: list[WatchlistItem] = []
    for ticker in list_tickers(user_id):
        update = price_cache.get(ticker)
        if update:
            items.append(
                WatchlistItem(
                    ticker=ticker,
                    price=update.price,
                    previous_price=update.previous_price,
                    change=update.change,
                    change_percent=update.change_percent,
                    direction=update.direction,
                    timestamp=update.timestamp,
                )
            )
        else:
            items.append(WatchlistItem(ticker=ticker))
    return items


async def add_ticker(
    ticker: str,
    source: MarketDataSource,
    user_id: str = settings.user_id,
) -> dict[str, Any]:
    ticker = ticker.strip().upper()
    if not ticker:
        raise WatchlistError("Ticker is required")

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        if existing:
            raise WatchlistError(f"{ticker} is already on the watchlist")
        conn.execute(
            """
            INSERT INTO watchlist (id, user_id, ticker, added_at)
            VALUES (?, ?, ?, ?)
            """,
            (new_id(), user_id, ticker, utc_now_iso()),
        )

    await source.add_ticker(ticker)
    return {"ticker": ticker, "action": "add"}


async def remove_ticker(
    ticker: str,
    source: MarketDataSource,
    user_id: str = settings.user_id,
) -> dict[str, Any]:
    ticker = ticker.strip().upper()
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        )
        if cur.rowcount == 0:
            raise WatchlistError(f"{ticker} is not on the watchlist")

    await source.remove_ticker(ticker)
    return {"ticker": ticker, "action": "remove"}
