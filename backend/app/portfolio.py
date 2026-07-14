"""Portfolio and trade execution logic."""

from __future__ import annotations

import logging
from typing import Any

from .config import settings
from .database import get_connection, new_id, utc_now_iso
from .market.cache import PriceCache
from .schemas import PortfolioOut, PositionOut, TradeResult

logger = logging.getLogger(__name__)


class TradeError(Exception):
    """Raised when a trade cannot be executed."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def get_cash(user_id: str = settings.user_id) -> float:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            raise TradeError("User profile not found")
        return float(row["cash_balance"])


def get_positions_raw(user_id: str = settings.user_id) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ticker, quantity, avg_cost, updated_at
            FROM positions
            WHERE user_id = ?
            ORDER BY ticker
            """,
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def build_portfolio(price_cache: PriceCache, user_id: str = settings.user_id) -> PortfolioOut:
    cash = get_cash(user_id)
    raw = get_positions_raw(user_id)

    positions: list[PositionOut] = []
    total_positions_value = 0.0
    total_cost = 0.0
    unrealized = 0.0

    for p in raw:
        ticker = p["ticker"]
        qty = float(p["quantity"])
        avg_cost = float(p["avg_cost"])
        price = price_cache.get_price(ticker)
        cost_basis = qty * avg_cost
        total_cost += cost_basis

        if price is not None:
            mv = qty * price
            pnl = mv - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis else 0.0
            total_positions_value += mv
            unrealized += pnl
        else:
            mv = None
            pnl = None
            pnl_pct = None

        positions.append(
            PositionOut(
                ticker=ticker,
                quantity=qty,
                avg_cost=round(avg_cost, 4),
                current_price=price,
                market_value=round(mv, 2) if mv is not None else None,
                unrealized_pnl=round(pnl, 2) if pnl is not None else None,
                unrealized_pnl_percent=round(pnl_pct, 4) if pnl_pct is not None else None,
            )
        )

    total_value = cash + total_positions_value
    for pos in positions:
        if pos.market_value is not None and total_value > 0:
            pos.weight = round(pos.market_value / total_value * 100, 2)
        else:
            pos.weight = 0.0

    starting = settings.default_cash
    total_return_pct = ((total_value - starting) / starting * 100) if starting else 0.0

    return PortfolioOut(
        cash_balance=round(cash, 2),
        positions=positions,
        total_positions_value=round(total_positions_value, 2),
        total_value=round(total_value, 2),
        unrealized_pnl=round(unrealized, 2),
        total_return_percent=round(total_return_pct, 4),
    )


def execute_trade(
    price_cache: PriceCache,
    ticker: str,
    quantity: float,
    side: str,
    user_id: str = settings.user_id,
) -> TradeResult:
    ticker = ticker.strip().upper()
    side = side.lower()
    if quantity <= 0:
        raise TradeError("Quantity must be positive")
    if side not in {"buy", "sell"}:
        raise TradeError("Side must be 'buy' or 'sell'")

    price = price_cache.get_price(ticker)
    if price is None:
        raise TradeError(f"No price available for {ticker}")

    now = utc_now_iso()

    with get_connection() as conn:
        profile = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not profile:
            raise TradeError("User profile not found")
        cash = float(profile["cash_balance"])

        pos = conn.execute(
            "SELECT id, quantity, avg_cost FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()

        if side == "buy":
            cost = quantity * price
            if cost > cash + 1e-9:
                raise TradeError(
                    f"Insufficient cash: need ${cost:.2f}, have ${cash:.2f}"
                )
            new_cash = cash - cost
            if pos:
                old_qty = float(pos["quantity"])
                old_avg = float(pos["avg_cost"])
                new_qty = old_qty + quantity
                new_avg = (old_qty * old_avg + quantity * price) / new_qty
                conn.execute(
                    """
                    UPDATE positions
                    SET quantity = ?, avg_cost = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new_qty, new_avg, now, pos["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (new_id(), user_id, ticker, quantity, price, now),
                )
            conn.execute(
                "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
                (new_cash, user_id),
            )
        else:
            if not pos:
                raise TradeError(f"No position in {ticker} to sell")
            old_qty = float(pos["quantity"])
            if quantity > old_qty + 1e-9:
                raise TradeError(
                    f"Insufficient shares: trying to sell {quantity}, own {old_qty}"
                )
            proceeds = quantity * price
            new_cash = cash + proceeds
            new_qty = old_qty - quantity
            if new_qty <= 1e-9:
                conn.execute("DELETE FROM positions WHERE id = ?", (pos["id"],))
            else:
                conn.execute(
                    """
                    UPDATE positions SET quantity = ?, updated_at = ? WHERE id = ?
                    """,
                    (new_qty, now, pos["id"]),
                )
            conn.execute(
                "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
                (new_cash, user_id),
            )

        trade_id = new_id()
        conn.execute(
            """
            INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (trade_id, user_id, ticker, side, quantity, price, now),
        )

    portfolio = build_portfolio(price_cache, user_id)
    record_snapshot(portfolio.total_value, user_id)

    trade = {
        "id": trade_id,
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "price": price,
        "executed_at": now,
    }
    return TradeResult(
        success=True,
        message=f"{'Bought' if side == 'buy' else 'Sold'} {quantity} {ticker} @ ${price:.2f}",
        trade=trade,
        portfolio=portfolio,
    )


def record_snapshot(total_value: float, user_id: str = settings.user_id) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (new_id(), user_id, total_value, utc_now_iso()),
        )


def get_history(user_id: str = settings.user_id, limit: int = 500) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT total_value, recorded_at
            FROM portfolio_snapshots
            WHERE user_id = ?
            ORDER BY recorded_at ASC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def compute_total_value(price_cache: PriceCache, user_id: str = settings.user_id) -> float:
    return build_portfolio(price_cache, user_id).total_value
