"""FinAlly FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import router as api_router
from .config import settings
from .database import init_db
from .market import PriceCache, create_market_data_source, create_stream_router
from .portfolio import compute_total_value, record_snapshot
from .state import AppState
from .watchlist import list_tickers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("finally")


async def _snapshot_loop(cache: PriceCache) -> None:
    while True:
        try:
            await asyncio.sleep(settings.snapshot_interval_seconds)
            total = compute_total_value(cache)
            record_snapshot(total)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Portfolio snapshot failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    cache = PriceCache()
    source = create_market_data_source(cache)
    tickers = list_tickers()
    if not tickers:
        tickers = list(settings.default_tickers)
    await source.start(tickers)
    snapshot_task = asyncio.create_task(_snapshot_loop(cache), name="portfolio-snapshots")

    app.state.app_state = AppState(
        price_cache=cache,
        market_source=source,
        snapshot_task=snapshot_task,
    )
    logger.info(
        "FinAlly started — db=%s tickers=%d mock_llm=%s massive=%s",
        settings.db_path,
        len(tickers),
        settings.llm_mock,
        bool(settings.massive_api_key),
    )
    try:
        yield
    finally:
        snapshot_task.cancel()
        try:
            await snapshot_task
        except asyncio.CancelledError:
            pass
        await source.stop()
        logger.info("FinAlly stopped")


def create_app() -> FastAPI:
    app = FastAPI(title="FinAlly", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins + ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    # Stream router needs cache — registered after startup via middleware pattern:
    # We attach routes that close over app.state at request time via a wrapper router.
    from fastapi import Request
    from fastapi.responses import StreamingResponse

    from .market.stream import _generate_events

    @app.get("/api/stream/prices")
    async def stream_prices(request: Request) -> StreamingResponse:
        st: AppState = request.app.state.app_state
        return StreamingResponse(
            _generate_events(st.price_cache, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Also keep factory available for tests
    _ = create_stream_router

    static_dir = settings.static_dir
    if static_dir.is_dir() and (static_dir / "index.html").exists():
        assets = static_dir / "_next"
        if assets.is_dir():
            app.mount("/_next", StaticFiles(directory=str(assets)), name="next-static")
        # Mount other static assets if present
        for name in ("icons", "images", "favicon.ico"):
            p = static_dir / name
            if p.is_dir():
                app.mount(f"/{name}", StaticFiles(directory=str(p)), name=name)

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str):
            from fastapi import HTTPException

            if full_path.startswith("api/") or full_path == "api":
                raise HTTPException(status_code=404, detail="Not Found")
            candidate = (static_dir / full_path).resolve()
            try:
                candidate.relative_to(static_dir.resolve())
            except ValueError as e:
                raise HTTPException(status_code=404, detail="Not Found") from e
            if candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(static_dir / "index.html")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(__import__("os").environ.get("PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    run()
