"""Pydantic request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class TradeRequest(BaseModel):
    ticker: str
    quantity: float = Field(gt=0)
    side: Literal["buy", "sell"]

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        t = v.strip().upper()
        if not t:
            raise ValueError("ticker is required")
        return t


class WatchlistAddRequest(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        t = v.strip().upper()
        if not t:
            raise ValueError("ticker is required")
        return t


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class PositionOut(BaseModel):
    ticker: str
    quantity: float
    avg_cost: float
    current_price: float | None
    market_value: float | None
    unrealized_pnl: float | None
    unrealized_pnl_percent: float | None
    weight: float | None = None


class PortfolioOut(BaseModel):
    cash_balance: float
    positions: list[PositionOut]
    total_positions_value: float
    total_value: float
    unrealized_pnl: float
    total_return_percent: float


class TradeResult(BaseModel):
    success: bool
    message: str
    trade: dict[str, Any] | None = None
    portfolio: PortfolioOut | None = None


class WatchlistItem(BaseModel):
    ticker: str
    price: float | None = None
    previous_price: float | None = None
    change: float | None = None
    change_percent: float | None = None
    direction: str | None = None
    timestamp: float | None = None


class SnapshotOut(BaseModel):
    total_value: float
    recorded_at: str


class LLMTrade(BaseModel):
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()


class LLMWatchlistChange(BaseModel):
    ticker: str
    action: Literal["add", "remove"]

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()


class LLMResponse(BaseModel):
    message: str
    trades: list[LLMTrade] = Field(default_factory=list)
    watchlist_changes: list[LLMWatchlistChange] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: str
    trades: list[dict[str, Any]] = Field(default_factory=list)
    watchlist_changes: list[dict[str, Any]] = Field(default_factory=list)
    trade_results: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
