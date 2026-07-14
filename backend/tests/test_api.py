"""API integration tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import init_db
from app.main import create_app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "api.db"
        monkeypatch.setattr(settings, "db_path", path)
        monkeypatch.setattr(settings, "llm_mock", True)
        monkeypatch.delenv("MASSIVE_API_KEY", raising=False)
        init_db(path)
        app = create_app()
        with TestClient(app) as c:
            yield c


def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_watchlist_default(client: TestClient):
    r = client.get("/api/watchlist")
    assert r.status_code == 200
    tickers = [x["ticker"] for x in r.json()]
    assert "AAPL" in tickers
    assert len(tickers) == 10


def test_portfolio_initial(client: TestClient):
    r = client.get("/api/portfolio")
    assert r.status_code == 200
    data = r.json()
    assert data["cash_balance"] == 10000.0
    assert data["positions"] == []


def test_trade_flow(client: TestClient):
    r = client.post(
        "/api/portfolio/trade",
        json={"ticker": "AAPL", "quantity": 5, "side": "buy"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["portfolio"]["cash_balance"] < 10000

    r2 = client.get("/api/portfolio")
    assert len(r2.json()["positions"]) == 1


def test_add_remove_watchlist(client: TestClient):
    r = client.post("/api/watchlist", json={"ticker": "AMD"})
    assert r.status_code == 200
    tickers = [x["ticker"] for x in client.get("/api/watchlist").json()]
    assert "AMD" in tickers

    r2 = client.delete("/api/watchlist/AMD")
    assert r2.status_code == 200
    tickers = [x["ticker"] for x in client.get("/api/watchlist").json()]
    assert "AMD" not in tickers


def test_chat_mock(client: TestClient):
    r = client.post("/api/chat", json={"message": "summarize my portfolio"})
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert len(data["message"]) > 0


def test_chat_mock_buy(client: TestClient):
    r = client.post("/api/chat", json={"message": "buy 2 AAPL"})
    assert r.status_code == 200
    data = r.json()
    assert data["trades"] or data["trade_results"]
    port = client.get("/api/portfolio").json()
    assert any(p["ticker"] == "AAPL" for p in port["positions"])
