"""Massive (Polygon.io) API client for real market data.

When the API key lacks snapshot access (free tier), the client
transparently falls back to the GBM simulator so the app still
streams live-looking prices without any user intervention.
"""

from __future__ import annotations

import asyncio
import logging

from massive import RESTClient
from massive.rest.models import SnapshotMarketType

from .cache import PriceCache
from .interface import MarketDataSource

logger = logging.getLogger(__name__)

# HTTP/API status strings that indicate missing entitlement
_NOT_ENTITLED = {"404", "NOT_AUTHORIZED", "403"}


class MassiveDataSource(MarketDataSource):
    """MarketDataSource backed by the Massive (Polygon.io) REST API.

    Polls GET /v2/snapshot/locale/us/markets/stocks/tickers for all watched
    tickers in a single API call, then writes results to the PriceCache.

    Rate limits:
      - Free tier: 5 req/min → poll every 15s (default)
      - Paid tiers: higher limits → poll every 2-5s
    """

    def __init__(
        self,
        api_key: str,
        price_cache: PriceCache,
        poll_interval: float = 15.0,
    ) -> None:
        self._api_key = api_key
        self._cache = price_cache
        self._interval = poll_interval
        self._tickers: list[str] = []
        self._task: asyncio.Task | None = None
        self._client: RESTClient | None = None
        self._fallback: "SimulatorDataSource | None" = None  # set if Massive is unavailable

    async def start(self, tickers: list[str]) -> None:
        self._client = RESTClient(api_key=self._api_key)
        self._tickers = list(tickers)

        # Do an immediate first poll so the cache has data right away.
        # If it fails with a permissions error, fall back to the simulator.
        probe_ok = await self._poll_once()
        if not probe_ok:
            logger.warning(
                "Massive API not accessible (free-tier key or wrong endpoint). "
                "Falling back to GBM simulator for price streaming."
            )
            from .simulator import SimulatorDataSource  # avoid circular at module level
            self._fallback = SimulatorDataSource(price_cache=self._cache)
            await self._fallback.start(tickers)
            return

        self._task = asyncio.create_task(self._poll_loop(), name="massive-poller")
        logger.info(
            "Massive poller started: %d tickers, %.1fs interval",
            len(tickers),
            self._interval,
        )

    async def stop(self) -> None:
        if self._fallback:
            await self._fallback.stop()
            self._fallback = None
            return
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        self._client = None
        logger.info("Massive poller stopped")

    async def add_ticker(self, ticker: str) -> None:
        ticker = ticker.upper().strip()
        if self._fallback:
            await self._fallback.add_ticker(ticker)
            return
        if ticker not in self._tickers:
            self._tickers.append(ticker)
            logger.info("Massive: added ticker %s (will appear on next poll)", ticker)

    async def remove_ticker(self, ticker: str) -> None:
        ticker = ticker.upper().strip()
        if self._fallback:
            await self._fallback.remove_ticker(ticker)
            return
        self._tickers = [t for t in self._tickers if t != ticker]
        self._cache.remove(ticker)
        logger.info("Massive: removed ticker %s", ticker)

    def get_tickers(self) -> list[str]:
        if self._fallback:
            return self._fallback.get_tickers()
        return list(self._tickers)

    # --- Internal ---

    async def _poll_loop(self) -> None:
        """Poll on interval. First poll already happened in start()."""
        while True:
            await asyncio.sleep(self._interval)
            await self._poll_once()

    async def _poll_once(self) -> bool:
        """Execute one poll cycle: fetch snapshots, update cache.

        Returns True if the poll succeeded (even partially), False if the API
        is inaccessible (404 / NOT_AUTHORIZED) so the caller can fall back.
        """
        if not self._tickers or not self._client:
            return True  # nothing to do, not a failure

        try:
            # The Massive RESTClient is synchronous — run in a thread to
            # avoid blocking the event loop.
            snapshots = await asyncio.to_thread(self._fetch_snapshots)
            processed = 0
            for snap in snapshots:
                try:
                    price = snap.last_trade.price
                    # Massive timestamps are Unix milliseconds → convert to seconds
                    timestamp = snap.last_trade.timestamp / 1000.0
                    self._cache.update(
                        ticker=snap.ticker,
                        price=price,
                        timestamp=timestamp,
                    )
                    processed += 1
                except (AttributeError, TypeError) as e:
                    logger.warning(
                        "Skipping snapshot for %s: %s",
                        getattr(snap, "ticker", "???"),
                        e,
                    )
            logger.debug("Massive poll: updated %d/%d tickers", processed, len(self._tickers))
            return True

        except Exception as e:
            err_str = str(e)
            # Detect free-tier / wrong-plan errors → signal caller to fall back
            if any(marker in err_str for marker in ("404", "NOT_AUTHORIZED", "403", "not entitled")):
                logger.warning("Massive API entitlement error: %s", e)
                return False
            logger.error("Massive poll failed: %s", e)
            return True  # Transient error — let the loop retry

    def _fetch_snapshots(self) -> list:
        """Synchronous call to the Massive REST API. Runs in a thread."""
        return self._client.get_snapshot_all(
            market_type=SnapshotMarketType.STOCKS,
            tickers=self._tickers,
        )
