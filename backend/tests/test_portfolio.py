"""Portfolio trade execution tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.config import settings
from app.database import init_db
from app.market.cache import PriceCache
from app.portfolio import TradeError, build_portfolio, execute_trade, get_history


@pytest.fixture()
def tmp_db(monkeypatch: pytest.MonkeyPatch):
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "test.db"
        monkeypatch.setattr(settings, "db_path", path)
        init_db(path)
        yield path


@pytest.fixture()
def cache() -> PriceCache:
    c = PriceCache()
    c.update("AAPL", 100.0)
    c.update("TSLA", 200.0)
    return c


def test_buy_and_portfolio(tmp_db, cache: PriceCache):
    result = execute_trade(cache, "AAPL", 10, "buy")
    assert result.success
    assert result.portfolio is not None
    assert result.portfolio.cash_balance == pytest.approx(9000.0)
    assert len(result.portfolio.positions) == 1
    assert result.portfolio.positions[0].ticker == "AAPL"
    assert result.portfolio.positions[0].quantity == 10


def test_insufficient_cash(tmp_db, cache: PriceCache):
    with pytest.raises(TradeError, match="Insufficient cash"):
        execute_trade(cache, "AAPL", 10_000, "buy")


def test_sell_more_than_owned(tmp_db, cache: PriceCache):
    execute_trade(cache, "AAPL", 5, "buy")
    with pytest.raises(TradeError, match="Insufficient shares"):
        execute_trade(cache, "AAPL", 10, "sell")


def test_sell_updates_cash(tmp_db, cache: PriceCache):
    execute_trade(cache, "AAPL", 10, "buy")
    # Price move
    cache.update("AAPL", 110.0)
    result = execute_trade(cache, "AAPL", 10, "sell")
    assert result.portfolio is not None
    assert result.portfolio.cash_balance == pytest.approx(10_100.0)
    assert result.portfolio.positions == []


def test_avg_cost_averaging(tmp_db, cache: PriceCache):
    execute_trade(cache, "AAPL", 10, "buy")  # @100
    cache.update("AAPL", 120.0)
    execute_trade(cache, "AAPL", 10, "buy")  # @120
    p = build_portfolio(cache)
    pos = p.positions[0]
    assert pos.quantity == 20
    assert pos.avg_cost == pytest.approx(110.0)


def test_history_records_trades(tmp_db, cache: PriceCache):
    execute_trade(cache, "AAPL", 1, "buy")
    hist = get_history()
    assert len(hist) >= 2  # seed + trade snapshot
