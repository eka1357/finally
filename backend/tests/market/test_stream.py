"""Tests for the SSE streaming endpoint factory."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI

from app.market.cache import PriceCache
from app.market.stream import _generate_events, create_stream_router


def _mock_request(*, disconnected: bool = False) -> MagicMock:
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.is_disconnected = AsyncMock(return_value=disconnected)
    return request


class TestCreateStreamRouter:
    def test_registers_prices_route(self):
        """Factory mounts GET /api/stream/prices on a fresh router."""
        cache = PriceCache()
        router = create_stream_router(cache)
        assert any(getattr(r, "path", "").endswith("/prices") for r in router.routes)

    def test_factory_is_idempotent(self):
        """Calling the factory twice must not double-register routes on one router."""
        cache = PriceCache()
        r1 = create_stream_router(cache)
        r2 = create_stream_router(cache)
        assert r1 is not r2
        assert len(r1.routes) == 1
        assert len(r2.routes) == 1

    def test_endpoint_is_wired_on_app(self):
        """Router can be mounted at /api/stream/prices without opening a stream."""
        cache = PriceCache()
        app = FastAPI()
        app.include_router(create_stream_router(cache))

        routes = [r for r in app.routes if getattr(r, "path", None) == "/api/stream/prices"]
        assert len(routes) == 1
        assert "GET" in routes[0].methods


@pytest.mark.asyncio
class TestGenerateEvents:
    async def test_yields_retry_then_data(self):
        cache = PriceCache()
        cache.update("AAPL", 190.5)
        request = _mock_request()

        # Disconnect after the first data-bearing poll cycle
        call_count = 0

        async def disconnect_after_data() -> bool:
            nonlocal call_count
            call_count += 1
            return call_count > 2

        request.is_disconnected = disconnect_after_data

        events: list[str] = []
        async for event in _generate_events(cache, request, interval=0.01):
            events.append(event)

        assert events[0] == "retry: 1000\n\n"
        data_events = [e for e in events if e.startswith("data: ")]
        assert len(data_events) >= 1
        payload = json.loads(data_events[0].removeprefix("data: ").strip())
        assert "AAPL" in payload
        assert payload["AAPL"]["price"] == 190.5

    async def test_stops_when_client_disconnects(self):
        cache = PriceCache()
        cache.update("AAPL", 100.0)
        request = _mock_request(disconnected=True)

        events = [event async for event in _generate_events(cache, request, interval=0.01)]
        # Only the initial retry directive before the disconnect check
        assert events == ["retry: 1000\n\n"]

    async def test_skips_emit_when_version_unchanged(self):
        cache = PriceCache()
        cache.update("AAPL", 100.0)
        request = _mock_request()

        call_count = 0

        async def disconnect_after_idle_polls() -> bool:
            nonlocal call_count
            call_count += 1
            return call_count > 4

        request.is_disconnected = disconnect_after_idle_polls

        events = [
            event async for event in _generate_events(cache, request, interval=0.01)
        ]
        data_events = [e for e in events if e.startswith("data: ")]
        # One emit on first version sighting; idle polls must not re-emit
        assert len(data_events) == 1
