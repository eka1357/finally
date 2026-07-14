"""LLM mock parsing tests."""

from app.llm import _mock_response
from app.schemas import PortfolioOut


def _empty_portfolio() -> PortfolioOut:
    return PortfolioOut(
        cash_balance=10000,
        positions=[],
        total_positions_value=0,
        total_value=10000,
        unrealized_pnl=0,
        total_return_percent=0,
    )


def test_mock_buy_parse():
    r = _mock_response("please buy 3 MSFT now", _empty_portfolio())
    assert r.trades
    assert r.trades[0].ticker == "MSFT"
    assert r.trades[0].quantity == 3
    assert r.trades[0].side == "buy"


def test_mock_watchlist_add():
    r = _mock_response("add PYPL to watchlist", _empty_portfolio())
    assert r.watchlist_changes
    assert r.watchlist_changes[0].ticker == "PYPL"
    assert r.watchlist_changes[0].action == "add"
