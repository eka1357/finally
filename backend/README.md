# FinAlly Backend

FastAPI backend: market data, portfolio, watchlist, SSE, and AI chat.

## Setup

```bash
uv sync --extra dev
```

## Run

```bash
# From repo root .env is auto-loaded
uv run uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
uv run pytest -v
uv run pytest --cov=app
uv run ruff check app/ tests/
```

## Demo (market data only)

```bash
uv run market_data_demo.py
```

## Layout

- `app/main.py` — FastAPI app + lifespan
- `app/api.py` — REST routes
- `app/market/` — simulator / Massive / SSE
- `app/portfolio.py` — trades & valuation
- `app/watchlist.py` — watchlist CRUD
- `app/chat.py` / `app/llm.py` — AI copilot
- `app/database.py` — SQLite schema + seed
