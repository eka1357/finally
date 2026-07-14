"""HTTP API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from .chat import get_chat_history, handle_chat
from .portfolio import TradeError, build_portfolio, execute_trade, get_history
from .schemas import ChatRequest, ChatResponse, TradeRequest, WatchlistAddRequest
from .state import AppState
from .watchlist import WatchlistError, add_ticker, get_watchlist, remove_ticker

router = APIRouter(prefix="/api")


def _state(request: Request) -> AppState:
    return request.app.state.app_state


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "finally"}


@router.get("/portfolio")
async def portfolio(request: Request) -> dict:
    st = _state(request)
    return build_portfolio(st.price_cache).model_dump()


@router.post("/portfolio/trade")
async def trade(body: TradeRequest, request: Request) -> dict:
    st = _state(request)
    try:
        result = execute_trade(st.price_cache, body.ticker, body.quantity, body.side)
        return result.model_dump()
    except TradeError as e:
        raise HTTPException(status_code=400, detail=e.message) from e


@router.get("/portfolio/history")
async def portfolio_history() -> list[dict]:
    return get_history()


@router.get("/watchlist")
async def watchlist(request: Request) -> list[dict]:
    st = _state(request)
    return [w.model_dump() for w in get_watchlist(st.price_cache)]


@router.post("/watchlist")
async def watchlist_add(body: WatchlistAddRequest, request: Request) -> dict:
    st = _state(request)
    try:
        return await add_ticker(body.ticker, st.market_source)
    except WatchlistError as e:
        raise HTTPException(status_code=400, detail=e.message) from e


@router.delete("/watchlist/{ticker}")
async def watchlist_remove(ticker: str, request: Request) -> dict:
    st = _state(request)
    try:
        return await remove_ticker(ticker, st.market_source)
    except WatchlistError as e:
        raise HTTPException(status_code=400, detail=e.message) from e


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    st = _state(request)
    return await handle_chat(body.message, st.price_cache, st.market_source)


@router.get("/chat/history")
async def chat_history() -> list[dict]:
    return get_chat_history()
