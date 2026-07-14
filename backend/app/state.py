"""Shared application state held on FastAPI app.state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .market.cache import PriceCache
from .market.interface import MarketDataSource


@dataclass
class AppState:
    price_cache: PriceCache
    market_source: MarketDataSource
    snapshot_task: Any = field(default=None)
